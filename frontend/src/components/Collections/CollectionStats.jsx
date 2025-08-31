// components/Collections/CollectionStats.jsx
import React from 'react';
import { TrendingUp, FileText, Rss, Users, Clock, Eye } from 'lucide-react';
import Card from '../Common/Card';

const CollectionStats = ({ collection }) => {
  const stats = collection?.stats || {
    totalArticles: 0,
    weeklyArticles: 0,
    activeFeeds: 0,
    activeMembers: 0
  };

  const statCards = [
    {
      icon: FileText,
      value: stats.totalArticles,
      label: 'Articles total',
      color: 'var(--primary-purple)'
    },
    {
      icon: TrendingUp,
      value: stats.weeklyArticles,
      label: 'Articles cette semaine',
      color: 'var(--success-green)'
    },
    {
      icon: Rss,
      value: stats.activeFeeds,
      label: 'Flux actifs',
      color: 'var(--info-blue)'
    },
    {
      icon: Users,
      value: stats.activeMembers,
      label: 'Membres actifs',
      color: 'var(--warning-orange)'
    }
  ];

  return (
    <>
      <div className="stats-grid">
        {statCards.map((stat, index) => (
          <div key={index} className="stat-card">
            <div className="stat-icon" style={{ color: stat.color }}>
              <stat.icon size={24} />
            </div>
            <div className="stat-number" style={{ color: stat.color }}>
              {stat.value}
            </div>
            <div className="stat-label">{stat.label}</div>
          </div>
        ))}
      </div>
      
      <Card>
        <div className="card-header">
          <h3 className="card-title">Activité récente</h3>
        </div>
        
        <div className="activity-preview">
          <div className="activity-item">
            <Clock size={16} />
            <span>Dernière mise à jour : Il y a 2 heures</span>
          </div>
          <div className="activity-item">
            <Eye size={16} />
            <span>Articles lus aujourd'hui : 12</span>
          </div>
          <div className="activity-item">
            <TrendingUp size={16} />
            <span>Croissance hebdomadaire : +15%</span>
          </div>
        </div>
        
        <div className="chart-placeholder">
          📊 Graphiques d'activité à venir
          <br /><br />
          Cette section contiendra des graphiques sur :
          <ul>
            <li>Évolution du nombre d'articles</li>
            <li>Activité des membres</li>
            <li>Sources les plus populaires</li>
            <li>Temps de lecture moyen</li>
          </ul>
        </div>
      </Card>

      <style jsx>{`
        .stat-card {
          background-color: var(--bg-white);
          padding: 1.5rem;
          border-radius: 8px;
          box-shadow: var(--shadow);
          text-align: center;
          transition: transform 0.2s;
        }

        .stat-card:hover {
          transform: translateY(-2px);
          box-shadow: var(--shadow-lg);
        }

        .stat-icon {
          margin-bottom: 1rem;
          display: flex;
          justify-content: center;
        }

        .stat-number {
          font-size: 2rem;
          font-weight: 700;
          margin-bottom: 0.5rem;
        }

        .stat-label {
          color: var(--text-gray);
          font-size: 0.9rem;
        }

        .activity-preview {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin-bottom: 2rem;
          padding: 1rem;
          background-color: var(--bg-light);
          border-radius: 8px;
        }

        .activity-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--text-gray);
          font-size: 0.9rem;
        }

        .chart-placeholder {
          color: var(--text-gray);
          text-align: center;
          padding: 3rem;
          background-color: var(--bg-light);
          border-radius: 8px;
          border: 2px dashed var(--border-light);
        }

        .chart-placeholder ul {
          text-align: left;
          display: inline-block;
          margin-top: 1rem;
        }

        .chart-placeholder li {
          margin: 0.5rem 0;
        }

        @media (max-width: 768px) {
          .stats-grid {
            grid-template-columns: 1fr 1fr;
          }
        }

        @media (max-width: 480px) {
          .stats-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </>
  );
};

export default CollectionStats;