import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  LinearProgress,
  Card,
  CardContent,
  Chip,
  CircularProgress,
} from '@mui/material';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { fetchDocuments, uploadDocument, clearDatabase } from '../api';

const stateConfig = {
  done: { color: 'success', icon: <CheckCircle size={16} />, label: 'Done' },
  processing: { color: 'warning', icon: <Loader2 size={16} />, label: 'Processing' },
  error: { color: 'error', icon: <AlertCircle size={16} />, label: 'Error' },
};

export default function DocumentsTab() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [file, setFile] = useState(null);
  const [clearing, setClearing] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const doLoad = async () => {
      try {
        const docs = await fetchDocuments();
        if (isMounted) setDocuments(docs);
      } catch (err) {
        console.error('Failed to load documents:', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    };
    doLoad();
    const interval = setInterval(doLoad, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await uploadDocument(file);
      setFile(null);
      // Refresh documents after upload
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error('Upload failed:', err);
      alert('Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleClear = async () => {
    if (!confirm('Are you sure you want to clear all documents? This cannot be undone.')) return;
    setClearing(true);
    try {
      await clearDatabase();
      const docs = await fetchDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error('Clear failed:', err);
      alert('Failed to clear database');
    } finally {
      setClearing(false);
    }
  };

  return (
    <Box sx={{ p: 4, height: '100%', overflow: 'auto' }}>
      <Box sx={{ maxWidth: 900, mx: 'auto' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 4 }}>
          <Typography variant="h4" component="h2" sx={{ fontWeight: 600 }}>
            Documents
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <Button
              variant="outlined"
              component="label"
              startIcon={<Upload size={18} />}
              sx={{ textTransform: 'none' }}
            >
              {file ? file.name : 'Choose File'}
              <input type="file" hidden onChange={handleFileChange} />
            </Button>
            <Button
              variant="contained"
              onClick={handleUpload}
              disabled={!file || uploading}
              startIcon={uploading ? <CircularProgress size={16} /> : <Upload size={18} />}
              sx={{ textTransform: 'none' }}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </Button>
            <Button
              variant="outlined"
              color="error"
              onClick={handleClear}
              disabled={clearing}
              sx={{ textTransform: 'none', ml: 1 }}
            >
              {clearing ? 'Clearing...' : 'Clear DB'}
            </Button>
          </Box>
        </Box>

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
            <CircularProgress />
          </Box>
        ) : documents.length === 0 ? (
          <Paper elevation={0} sx={{ p: 6, textAlign: 'center', bgcolor: 'background.paper' }}>
            <FileText size={48} color="#334155" style={{ margin: '0 auto 16px' }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No documents yet
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Upload your first document to start building the knowledge graph.
            </Typography>
          </Paper>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {documents.map((doc) => {
              const state = stateConfig[doc.state] || { color: 'default', icon: null, label: doc.state };

  return (
                <Card key={doc.uid} variant="outlined" sx={{ bgcolor: 'background.paper' }}>
                  <CardContent sx={{ p: 2.5, '&:last-child': { pb: 2.5 } }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <FileText size={20} color="#60a5fa" />
                        <Typography variant="h6" component="h3" sx={{ fontWeight: 500 }}>
                          {doc.name}
                        </Typography>
                      </Box>
                      <Chip
                        icon={state.icon}
                        label={state.label}
                        color={state.color}
                        size="small"
                        sx={{ fontWeight: 500, textTransform: 'capitalize' }}
                      />
                    </Box>

                    <Box sx={{ mb: 1.5 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                        <Typography variant="body2" color="text.secondary">
                          Progress
                        </Typography>
                        <Typography variant="body2" color="text.secondary" fontWeight={500}>
                          {doc.percent}%
                        </Typography>
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={doc.percent}
                        sx={{
                          height: 8,
                          borderRadius: 4,
                          bgcolor: 'rgba(255,255,255,0.05)',
                          '& .MuiLinearProgress-bar': {
                            borderRadius: 4,
                          },
                        }}
                      />
                    </Box>

                    <Typography variant="body2" color="text.secondary">
                      {doc.blocks_count} blocks extracted
                    </Typography>
                  </CardContent>
                </Card>
              );
            })}
          </Box>
        )}
      </Box>
    </Box>
  );
}
