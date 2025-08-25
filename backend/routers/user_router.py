# routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt

from dtos.user_dto import (
    UserRegisterDTO,
    UserLoginDTO,
    OAuth2LoginDTO,
    UserUpdateDTO,
    UserPreferencesDTO,
    PasswordChangeDTO,
    PasswordResetRequestDTO,
    PasswordResetDTO,
    UserResponseDTO,
    UserStatsDTO,
    TokenResponseDTO
)
from business.user_business import UserBusiness
from core.database import get_db
from core.security import verify_token, create_access_token, create_refresh_token
from core.config import settings

router = APIRouter(prefix="/api/users", tags=["Utilisateurs"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/users/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """Récupère l'utilisateur actuel depuis le token JWT"""
    try:
        payload = verify_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide"
            )
        
        user_business = UserBusiness(db)
        user = user_business.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide"
        )

@router.post("/register", response_model=UserResponseDTO, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegisterDTO,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Inscription d'un nouvel utilisateur"""
    user_business = UserBusiness(db)
    
    # Vérifier l'unicité de l'email et du nom d'utilisateur
    if user_business.email_exists(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà utilisé"
        )
    
    if user_business.username_exists(user_data.nom_utilisateur):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce nom d'utilisateur est déjà pris"
        )
    
    # Créer l'utilisateur
    user = user_business.create_user(user_data)
    
    # Envoyer email de vérification en arrière-plan
    background_tasks.add_task(
        user_business.send_verification_email,
        user.email,
        user.id
    )
    
    return user

@router.post("/login", response_model=TokenResponseDTO)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Connexion utilisateur avec email et mot de passe"""
    user_business = UserBusiness(db)
    
    # Authentifier l'utilisateur
    user = user_business.authenticate_user(
        form_data.username,  # Ici username est en fait l'email
        form_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Créer les tokens
    access_token = create_access_token({"user_id": user.id})
    refresh_token = create_refresh_token({"user_id": user.id})
    
    # Mettre à jour la dernière connexion
    user_business.update_last_login(user.id)
    
    return TokenResponseDTO(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponseDTO.from_orm(user)
    )

@router.post("/oauth2/login", response_model=TokenResponseDTO)
async def oauth2_login(
    oauth_data: OAuth2LoginDTO,
    db: Session = Depends(get_db)
):
    """Connexion via OAuth2 (Google, Microsoft, GitHub)"""
    user_business = UserBusiness(db)
    
    # Valider le token OAuth2 avec le provider
    user_info = user_business.validate_oauth2_token(
        oauth_data.provider,
        oauth_data.token
    )
    
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token OAuth2 invalide"
        )
    
    # Créer ou récupérer l'utilisateur
    user = user_business.get_or_create_oauth_user(
        provider=oauth_data.provider,
        email=user_info['email'],
        provider_user_id=user_info.get('user_id', user_info['email']),
        nom_utilisateur=user_info.get('username'),
        prenom=user_info.get('given_name'),
        nom=user_info.get('family_name'),
        access_token=oauth_data.token
    )
    
    # Créer les tokens
    access_token = create_access_token({"user_id": user.id})
    refresh_token = create_refresh_token({"user_id": user.id})
    
    return TokenResponseDTO(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="Bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponseDTO.from_orm(user)
    )

@router.get("/me", response_model=UserResponseDTO)
async def get_current_user_profile(
    current_user = Depends(get_current_user)
):
    """Récupère le profil de l'utilisateur connecté"""
    return UserResponseDTO.from_orm(current_user)

@router.put("/me", response_model=UserResponseDTO)
async def update_profile(
    user_update: UserUpdateDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour le profil de l'utilisateur"""
    user_business = UserBusiness(db)
    
    # Vérifier l'unicité si changement d'email ou username
    if user_update.email and user_update.email != current_user.email:
        if user_business.email_exists(user_update.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cet email est déjà utilisé"
            )
    
    if user_update.nom_utilisateur and user_update.nom_utilisateur != current_user.nom_utilisateur:
        if user_business.username_exists(user_update.nom_utilisateur):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce nom d'utilisateur est déjà pris"
            )
    
    updated_user = user_business.update_user(current_user.id, user_update)
    return UserResponseDTO.from_orm(updated_user)

@router.put("/me/preferences", response_model=UserResponseDTO)
async def update_preferences(
    preferences: UserPreferencesDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour les préférences de l'utilisateur"""
    user_business = UserBusiness(db)
    updated_user = user_business.update_preferences(current_user.id, preferences)
    return UserResponseDTO.from_orm(updated_user)

@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    password_data: PasswordChangeDTO,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change le mot de passe de l'utilisateur"""
    user_business = UserBusiness(db)
    
    # Vérifier l'ancien mot de passe
    if not user_business.verify_password(
        current_user.id,
        password_data.ancien_mot_de_passe
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ancien mot de passe incorrect"
        )
    
    # Changer le mot de passe
    user_business.change_password(current_user.id, password_data.nouveau_mot_de_passe)
    return None

@router.post("/password-reset/request", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    reset_request: PasswordResetRequestDTO,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Demande de réinitialisation de mot de passe"""
    user_business = UserBusiness(db)
    
    user = user_business.get_user_by_email(reset_request.email)
    if user:
        # Générer et envoyer le token de reset
        token = user_business.generate_reset_token(user.id)
        background_tasks.add_task(
            user_business.send_reset_password_email,
            user.email,
            token
        )
    
    # Toujours retourner 204 pour éviter l'énumération d'emails
    return None

@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    reset_data: PasswordResetDTO,
    db: Session = Depends(get_db)
):
    """Réinitialise le mot de passe avec le token"""
    user_business = UserBusiness(db)
    
    # Valider le token et réinitialiser le mot de passe
    if not user_business.reset_password_with_token(
        reset_data.token,
        reset_data.nouveau_mot_de_passe
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou expiré"
        )
    
    return None

@router.get("/me/stats", response_model=UserStatsDTO)
async def get_user_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les statistiques de l'utilisateur"""
    user_business = UserBusiness(db)
    stats = user_business.get_user_statistics(current_user.id)
    return stats

@router.post("/verify-email/{token}", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Vérifie l'email de l'utilisateur avec le token"""
    user_business = UserBusiness(db)
    
    if not user_business.verify_email_with_token(token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou expiré"
        )
    
    return None

@router.post("/refresh-token", response_model=TokenResponseDTO)
async def refresh_access_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """Rafraîchit le token d'accès avec le refresh token"""
    try:
        payload = verify_token(refresh_token, is_refresh=True)
        user_id = payload.get("user_id")
        
        user_business = UserBusiness(db)
        user = user_business.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Utilisateur non trouvé"
            )
        
        # Créer un nouveau token d'accès
        access_token = create_access_token({"user_id": user.id})
        
        return TokenResponseDTO(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponseDTO.from_orm(user)
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token invalide"
        )

@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    password: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime le compte de l'utilisateur (soft delete)"""
    user_business = UserBusiness(db)
    
    # Vérifier le mot de passe
    if not user_business.verify_password(current_user.id, password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe incorrect"
        )
    
    # Soft delete du compte
    user_business.soft_delete_user(current_user.id)
    return None