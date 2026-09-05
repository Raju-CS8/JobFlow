
import '../styles/Sidebar.css';

function Sidebar({ jobs, currentView, onNavigate }) {
  const stats = {
    pending: jobs.filter(j => j.status === 'PENDING').length,
    running: jobs.filter(j => j.status === 'RUNNING').length,
    completed: jobs.filter(j => j.status === 'COMPLETED').length,
    failed: jobs.filter(j => j.status === 'FAILED').length,
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h1>JobFlow</h1>
        <p className="tagline">Background Job Processing</p>
      </div>

      <nav className="sidebar-nav">
        <button
          className={`nav-item ${currentView === 'list' ? 'active' : ''}`}
          onClick={() => onNavigate('list')}
        >
          <span className="nav-icon">📋</span>
          <span className="nav-label">Jobs</span>
        </button>
        <button
          className={`nav-item ${currentView === 'submit' ? 'active' : ''}`}
          onClick={() => onNavigate('submit')}
        >
          <span className="nav-icon">➕</span>
          <span className="nav-label">Submit Job</span>
        </button>
      </nav>

      <div className="sidebar-stats">
        <h3>Status Summary</h3>
        <div className="stat-row">
          <span className="stat-label">Pending</span>
          <span className="stat-value pending">{stats.pending}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Running</span>
          <span className="stat-value running">{stats.running}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Completed</span>
          <span className="stat-value completed">{stats.completed}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Failed</span>
          <span className="stat-value failed">{stats.failed}</span>
        </div>
      </div>

      <div className="sidebar-footer">
        <p className="version">v0.1.0</p>
      </div>
    </aside>
  );
}

export default Sidebar;