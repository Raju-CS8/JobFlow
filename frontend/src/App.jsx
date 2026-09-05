import { useState, useEffect } from 'react';
import './App.css';
import JobList from './components/JobList';
import JobDetail from './components/JobDetail';
import SubmitJob from './components/SubmitJob';
import Sidebar from './components/Sidebar';
import { fetchJobs, fetchJob } from './api';

function App() {
  const [view, setView] = useState('list');
  const [jobs, setJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadJobs = async () => {
      try {
        setLoading(true);
        const data = await fetchJobs();
        setJobs(data);
      } catch (error) {
        console.error('Failed to fetch jobs:', error);
      } finally {
        setLoading(false);
      }
    };

    loadJobs();
    const interval = setInterval(loadJobs, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleSelectJob = async (jobId) => {
    try {
      const job = await fetchJob(jobId);
      setSelectedJob(job);
      setView('detail');
    } catch (error) {
      console.error('Failed to fetch job:', error);
    }
  };

  const handleJobSubmitted = () => {
    setView('list');
  };

  const handleBack = () => {
    setSelectedJob(null);
    setView('list');
  };

  return (
    <div className="app">
      <Sidebar
        jobs={jobs}
        currentView={view}
        onNavigate={setView}
      />
      <main className="main-content">
        {view === 'submit' && (
          <SubmitJob onSuccess={handleJobSubmitted} />
        )}
        {view === 'list' && (
          <JobList
            jobs={jobs}
            loading={loading}
            onSelectJob={handleSelectJob}
            onSubmitNew={() => setView('submit')}
          />
        )}
        {view === 'detail' && selectedJob && (
          <JobDetail job={selectedJob} onBack={handleBack} />
        )}
      </main>
    </div>
  );
}

export default App;