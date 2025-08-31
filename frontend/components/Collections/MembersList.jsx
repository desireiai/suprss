// src/components/Collections/MembersList.jsx
import React, { useState } from 'react';
import { useApp } from '../../hooks/useApp';
import Card from '../Common/Card';
import Button from '../Common/Button';

const MembersList = ({ collection }) => {
  const { addMemberToCollection, updateMemberPermissions } = useApp();
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('reader');

  const handleInvite = () => {
    if (inviteEmail && inviteEmail.includes('@')) {
      const newMember = {
        name: inviteEmail.split('@')[0],
        email: inviteEmail,
        initials: inviteEmail.substring(0, 2).toUpperCase(),
        role: inviteRole,
        permissions: inviteRole === 'reader' 
          ? ['read'] 
          : inviteRole === 'contributor'
          ? ['read', 'add', 'comment']
          : ['read', 'add', 'edit', 'comment']
      };
      
      addMemberToCollection(collection.id, newMember);
      setInviteEmail('');
      setInviteRole('reader');
      alert('Invitation envoyée !');
    }
  };

  const handlePermissionChange = (memberId, permission, checked) => {
    const member = collection.members.find(m => m.id === memberId);
    if (member && member.role !== 'creator') {
      const currentPermissions = member.permissions || [];
      const newPermissions = checked
        ? [...currentPermissions, permission]
        : currentPermissions.filter(p => p !== permission);
      
      updateMemberPermissions(collection.id, memberId, newPermissions);
    }
  };

  const permissions = [
    { id: 'read', label: 'Lecture' },
    { id: 'add', label: 'Ajout de flux' },
    { id: 'edit', label: 'Modification' },
    { id: 'comment', label: 'Commentaires' }
  ];

  return (
    <>
      <Card>
        <div className="card-header">
          <h3 className="card-title">Membres de la collection</h3>
        </div>
        
        <div className="alert alert-info">
          En tant que créateur de cette collection, vous avez tous les droits. 
          Vous pouvez définir les permissions pour chaque membre.
        </div>
        
        <div className="members-list">
          {collection?.members?.map(member => (
            <div key={member.id} className="member-item">
              <div className="member-info">
                <div className="member-avatar">{member.initials}</div>
                <div className="member-details">
                  <h4>
                    {member.name} 
                    {member.role === 'creator' && ' (Créateur)'}
                  </h4>
                  <div className="member-role">
                    {member.role === 'creator' ? 'Tous les droits' : 
                     member.role === 'member' ? 'Membre actif' : 'Lecteur'}
                  </div>
                </div>
              </div>
              <div className="permissions-grid">
                {permissions.map(permission => (
                  <div key={permission.id} className="permission-item">
                    <input
                      type="checkbox"
                      className="checkbox"
                      checked={member.permissions?.includes(permission.id) || false}
                      disabled={member.role === 'creator'}
                      onChange={(e) => 
                        handlePermissionChange(member.id, permission.id, e.target.checked)
                      }
                    />
                    <label>{permission.label}</label>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card style={{ marginTop: '2rem' }}>
        <div className="card-header">
          <h3 className="card-title">Inviter de nouveaux membres</h3>
        </div>
        
        <div className="invite-form">
          <div className="form-group">
            <label className="form-label">Email du membre</label>
            <input 
              type="email" 
              className="form-input" 
              placeholder="exemple@email.com"
              value={inviteEmail}
              onChange={(e) => setInviteEmail(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Rôle par défaut</label>
            <select 
              className="form-input form-select"
              value={inviteRole}
              onChange={(e) => setInviteRole(e.target.value)}
            >
              <option value="reader">Lecteur</option>
              <option value="contributor">Contributeur</option>
              <option value="moderator">Modérateur</option>
            </select>
          </div>
          <Button variant="primary" onClick={handleInvite}>
            Inviter
          </Button>
        </div>
      </Card>
    </>
  );
};

export default MembersList;