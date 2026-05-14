import { useState, useEffect, useCallback, useRef } from 'react';
import io from 'socket.io-client';
import ReactMarkdown from 'react-markdown';
import {
  Box,
  TextField,
  Button,
  Paper,
  Typography,
  CircularProgress,
} from '@mui/material';
import { Search, RotateCcw } from 'lucide-react';
import GraphPanel from './GraphPanel';
import NodeDetails from './NodeDetails';
import { fetchGraph, fetchNode, submitSearch } from '../api';

function MarkdownWithKgLinks({ children, onKgLink }) {
  return (
    <ReactMarkdown
        urlTransform={(url) => url}
      components={{
        a: ({ href, children, ...props }) => {
          if (href && href.startsWith('kg://')) {
            return (
              <a
                href={href}
                onClick={(e) => {
                  e.preventDefault();
                  const url = new URL(href);
                  const host = url.hostname; // e.g. "entity", "fact", "doc"
                  const pathParts = url.pathname.split('/').filter(Boolean);
                  if (host === 'entity' && pathParts[0]) {
                    onKgLink(pathParts[0], 'entity');
                  } else if (host === 'fact' && pathParts[0]) {
                    onKgLink(pathParts[0], 'fact');
                  } else if (host === 'doc' && pathParts[0]) {
                    onKgLink(pathParts[0], 'doc');
                  }
                }}
                style={{ color: '#60a5fa', cursor: 'pointer', textDecoration: 'underline' }}
                {...props}
              >
                {children}
              </a>
            );
          }
          return (
            <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
              {children}
            </a>
          );
        },
      }}
    >
      {children}
    </ReactMarkdown>
  );
}

export default function SearchTab() {
  const [query, setQuery] = useState('');
  const [report, setReport] = useState('');
  const [searching, setSearching] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [selectedUids, setSelectedUids] = useState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const socketRef = useRef(null);
  const graphPanelRef = useRef(null);

  useEffect(() => {
    let isMounted = true;
    const doLoad = async () => {
      try {
        const data = await fetchGraph();
        const nodes = Object.entries(data.nodes).map(([uid, node]) => ({
          uid,
          ...node,
          id: uid,
        }));
        const links = data.connections.map(([source, target, type]) => ({
          source,
          target,
          type,
          id: `${source}-${target}-${type}`,
        }));
        if (isMounted) setGraphData({ nodes, links });
      } catch (err) {
        console.error('Failed to load graph:', err);
      }
    };
    doLoad();
    return () => { isMounted = false; };
  }, []);

  const handleSearch = async () => {
    if (!query.trim() || searching) return;

    setSearching(true);
    setReport('');
    setSelectedUids([]);
    setSelectedNode(null);

    try {
      const { session_id } = await submitSearch(query);

      const socket = io('http://localhost:8000');
      socketRef.current = socket;

      socket.on('connect', () => {
        socket.emit('join_search', { session_id });
      });

      socket.on('report_update', (data) => {
        setReport(data.report);
      });

      socket.on('selection_update', (data) => {
        setSelectedUids((prev) => {
          const newUids = data.uids || [];
          const merged = [...prev, ...newUids];
          return [...new Set(merged)];
        });
      });

      socket.on('done', () => {
        setSearching(false);
        socket.disconnect();
      });

      socket.on('error', (err) => {
        console.error('Socket error:', err);
        setSearching(false);
        socket.disconnect();
      });
    } catch (err) {
      console.error('Search failed:', err);
      setSearching(false);
    }
  };

  const handleRestart = () => {
    setQuery('');
    setReport('');
    setSelectedUids([]);
    setSelectedNode(null);
    setSearching(false);
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
  };

  const handleNodeClick = useCallback(async (node) => {
    try {
      const details = await fetchNode(node.uid);
      setSelectedNode(details);
    } catch (err) {
      console.error('Failed to fetch node details:', err);
      setSelectedNode(node);
    }
  }, []);

  const handleKgLink = useCallback(
    (identifier, kind) => {
      let targetNode;
      if (kind === 'doc') {
        targetNode = graphData.nodes.find(
          (n) => n.node_class === 'document' && n.name === identifier
        );
      } else {
        targetNode = graphData.nodes.find((n) => n.uid === identifier);
      }

      if (!targetNode) {
        console.warn('Node not found for kg link:', identifier, kind);
        return;
      }

      handleNodeClick(targetNode);

      if (graphPanelRef.current && graphPanelRef.current.focusNode) {
        graphPanelRef.current.focusNode(targetNode);
      }
    },
    [graphData.nodes, handleNodeClick]
  );

  return (
    <Box sx={{ display: 'flex', height: '100%' }}>
      <Box sx={{ width: '50%', display: 'flex', flexDirection: 'column', borderRight: 1, borderColor: 'rgba(255,255,255,0.05)' }}>
        <Box sx={{ flex: 1, position: 'relative' }}>
          <GraphPanel
            ref={graphPanelRef}
            graphData={graphData}
            selectedUids={selectedUids}
            onNodeClick={handleNodeClick}
            searching={searching}
          />
          {searching && (
            <Box sx={{
              position: 'absolute',
              top: 16,
              left: '50%',
              transform: 'translateX(-50%)',
              bgcolor: 'background.paper',
              px: 3,
              py: 1.5,
              borderRadius: 2,
              border: 1,
              borderColor: 'rgba(255,255,255,0.05)',
              display: 'flex',
              alignItems: 'center',
              gap: 1,
              zIndex: 10,
            }}>
              <CircularProgress size={16} thickness={5} />
              <Typography variant="body2" color="text.secondary">
                Searching...
              </Typography>
            </Box>
          )}
        </Box>
        <Box sx={{ height: '20%', minHeight: 150 }}>
          <NodeDetails node={selectedNode} />
        </Box>
      </Box>

      <Box sx={{ width: '50%', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
        <Box sx={{ p: 2, borderBottom: 1, borderColor: 'rgba(255,255,255,0.05)' }}>
          <Box sx={{ display: 'flex', gap: 1.5 }}>
            <TextField
              fullWidth
              variant="outlined"
              size="small"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Enter your search query..."
              disabled={searching}
              sx={{
                '& .MuiOutlinedInput-root': {
                  bgcolor: 'background.paper',
                },
              }}
            />
            <Button
              variant="contained"
              onClick={handleSearch}
              disabled={searching || !query.trim()}
              startIcon={<Search size={18} />}
              sx={{ px: 3, whiteSpace: 'nowrap' }}
            >
              {searching ? 'Searching' : 'Search'}
            </Button>
          </Box>
        </Box>

        <Box sx={{ flex: 1, overflow: 'auto', p: 3 }}>
          {!report && !searching && (
            <Box sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: 2,
            }}>
              <Search size={48} color="#333333" />
              <Typography variant="body1" color="text.secondary">
                Enter a query and click Search to see results
              </Typography>
            </Box>
          )}

          {report && (
            <Paper elevation={0} sx={{ p: 3, bgcolor: 'background.paper' }}>
              <div className="markdown-body">
                <MarkdownWithKgLinks onKgLink={handleKgLink}>
                  {report}
                </MarkdownWithKgLinks>
              </div>
            </Paper>
          )}
        </Box>

        {(report || searching) && (
          <Box sx={{ p: 2, borderTop: 1, borderColor: 'rgba(255,255,255,0.05)' }}>
            <Button
              variant="outlined"
              onClick={handleRestart}
              startIcon={<RotateCcw size={18} />}
              sx={{ textTransform: 'none' }}
            >
              Restart
            </Button>
          </Box>
        )}
      </Box>
    </Box>
  );
}
