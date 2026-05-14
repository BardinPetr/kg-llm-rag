import { useState, useEffect, useRef, useCallback, useMemo, forwardRef, useImperativeHandle } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import SpriteText from 'three-spritetext';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Checkbox,
  FormGroup,
  FormControlLabel,
} from '@mui/material';
import { Filter } from 'lucide-react';

const normalizeNodeClass = (cls) => {
  const map = {
    DDocument: 'document',
    DBlock: 'block',
    KEntity: 'entity',
    KValFact: 'vfact',
    KRelFact: 'rfact'
  };
  return map[cls] || cls;
};

const NODE_COLORS = {
  entity: '#3b82f6',
  vfact: '#22c55e',
  rfact: '#f97316',
  document: '#a855f7',
  block: '#a438a6',
};

const EDGE_COLORS = {
  D_IN: '#94a3b8',
  K_PROOF: '#ec4899',
  K_SUBJ: '#6366f1',
  K_OBJ: '#10b981',
};

const EDGE_DEFAULT_COLOR = '#475569';
const DIMMED_GRAY = '#334155';

const NODE_CLASS_LABELS = {
  document: 'Document',
  block: 'Block',
  entity: 'Entity',
  vfact: 'ValFact',
  rfact: 'RelFact',
};

const ALL_NODE_CLASSES = ['entity', 'vfact', 'rfact', 'document', 'block'];
const DEFAULT_VISIBLE_CLASSES = ['entity', 'vfact', 'rfact'];

const GraphPanel = forwardRef(function GraphPanel({ graphData, selectedUids, onNodeClick, searching }, ref) {
  const fgRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef();
  const [visibleClasses, setVisibleClasses] = useState(DEFAULT_VISIBLE_CLASSES);
  const [showFilters, setShowFilters] = useState(false);

  const displayDataRef = useRef({ nodes: [], links: [] });

  useImperativeHandle(ref, () => ({
    focusNode: (nodeOrUid) => {
      if (!fgRef.current || !nodeOrUid) return;

      const graphNodes = displayDataRef.current.nodes;
      const target = typeof nodeOrUid === 'string'
        ? graphNodes.find((n) => n.uid === nodeOrUid)
        : graphNodes.find((n) => n.uid === (nodeOrUid.uid || nodeOrUid.id));

      if (!target) {
        console.warn('focusNode: node not found in graph data');
        return;
      }

      if (target.x == null || target.y == null || target.z == null) {
        setTimeout(() => {
          const retryNode = graphNodes.find((n) => n.uid === target.uid);
          if (retryNode && retryNode.x != null) {
            const distance = 200;
            const distRatio = 1 + distance / Math.hypot(retryNode.x, retryNode.y, retryNode.z);
            fgRef.current.cameraPosition(
              { x: retryNode.x * distRatio, y: retryNode.y * distRatio, z: retryNode.z * distRatio },
              retryNode,
              2500
            );
          }
        }, 500);
        return;
      }

      const distance = 200;
      const distRatio = 1 + distance / Math.hypot(target.x, target.y, target.z);
      fgRef.current.cameraPosition(
        { x: target.x * distRatio, y: target.y * distRatio, z: target.z * distRatio },
        target,
        2500
      );
    },
  }));

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width, height });
      }
    };
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const displayData = useMemo(() => {
    const rawNodes = (graphData.nodes || []).map((n) => ({
      ...n,
      node_class: normalizeNodeClass(n.node_class),
    }));

    const visibleSet = new Set(visibleClasses && visibleClasses.length > 0 ? visibleClasses : ALL_NODE_CLASSES);
    const nodes = rawNodes.filter((n) => visibleSet.has(n.node_class));
    const nodeUids = new Set(nodes.map((n) => n.uid));

    const rawLinks = graphData.links || [];
    const links = rawLinks
      .filter((l) => {
        const sUid = typeof l.source === 'string' ? l.source : l.source?.uid;
        const tUid = typeof l.target === 'string' ? l.target : l.target?.uid;
        return nodeUids.has(sUid) && nodeUids.has(tUid);
      })
      .map((l) => ({
        id: l.id,
        source: typeof l.source === 'string' ? l.source : l.source?.uid,
        target: typeof l.target === 'string' ? l.target : l.target?.uid,
        type: l.type || '',
      }));

    return { nodes, links };
  }, [graphData, visibleClasses]);

  useEffect(() => {
    displayDataRef.current = displayData;
  }, [displayData]);

  const isNodeSelected = useCallback(
    (node) => {
      if (!selectedUids || selectedUids.length === 0) return false;
      return selectedUids.includes(node.uid);
    },
    [selectedUids]
  );

  const isLinkSelected = useCallback(
    (link) => {
      if (!selectedUids || selectedUids.length === 0) return false;
      return (
        selectedUids.includes(link.source?.uid || link.source) ||
        selectedUids.includes(link.target?.uid || link.target)
      );
    },
    [selectedUids]
  );

  const getNodeColor = useCallback(
    (node) => {
      const normalizedClass = normalizeNodeClass(node.node_class);
      if (searching && selectedUids && selectedUids.length > 0) {
        if (isNodeSelected(node)) {
          return NODE_COLORS[normalizedClass] || '#888888';
        }
        return '#64748b';
      }
      return NODE_COLORS[normalizedClass] || '#888888';
    },
    [selectedUids, isNodeSelected, searching]
  );

  const getLinkColor = useCallback(
    (link) => {
      const type = link.type || '';
      const baseColor = EDGE_COLORS[type] || EDGE_DEFAULT_COLOR;
      if (searching && selectedUids && selectedUids.length > 0) {
        return isLinkSelected(link) ? baseColor : DIMMED_GRAY;
      }
      return baseColor;
    },
    [selectedUids, isLinkSelected, searching]
  );

  const nodeLabel = useCallback((node) => {
    const cls = normalizeNodeClass(node.node_class);
    if (cls === 'entity') {
      return (node.repr || node.uid).substring(0, 22);
    }
    if (cls === 'vfact' || cls === 'rfact') {
      return node.type_code || node.uid;
    }
    return node.name || node.uid;
  }, []);

  const nodeVal = useCallback((node) => {
    switch (normalizeNodeClass(node.node_class)) {
      case 'entity':
        return 4;
      case 'document':
        return 6;
      case 'block':
        return 3;
      case 'vfact':
        return 2;
      case 'rfact':
        return 2;
      default:
        return 2;
    }
  }, []);

  const nodeThreeObject = useCallback(
    (node) => {
      const label = nodeLabel(node);
      const sprite = new SpriteText(label);
      sprite.color = getNodeColor(node);
      sprite.textHeight = 3;
      sprite.center.y = -0.8;
      sprite.fontWeight = '500';
      return sprite;
    },
    [nodeLabel, getNodeColor]
  );

  const handleToggleClass = (cls) => {
    setVisibleClasses((prev) =>
      prev.includes(cls) ? prev.filter((c) => c !== cls) : [...prev, cls]
    );
  };

  return (
    <Box ref={containerRef} sx={{ width: '100%', height: '100%', position: 'relative' }}>
      <ForceGraph3D
        ref={fgRef}
        width={dimensions.width}
        height={dimensions.height}
        graphData={displayData}
        backgroundColor="#0a0a0a"
        nodeColor={getNodeColor}
        nodeVal={nodeVal}
        nodeLabel={nodeLabel}
        nodeThreeObjectExtend={true}
        nodeThreeObject={nodeThreeObject}
        linkColor={getLinkColor}
        linkWidth={0.5}
        linkOpacity={0.6}
        linkDirectionalArrowLength={6}
        linkDirectionalArrowRelPos={1}
        onNodeClick={onNodeClick}
        enableNavigationControls={true}
        showNavInfo={true}
        enableNodeDrag={true}
      />

      <Paper
        elevation={2}
        sx={{
          position: 'absolute',
          top: 12,
          right: 12,
          p: 1,
          bgcolor: 'rgba(10, 10, 10, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 10,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <IconButton
          size="small"
          onClick={() => setShowFilters((s) => !s)}
          color={showFilters ? 'primary' : 'default'}
          sx={{ border: 1, borderColor: 'rgba(255,255,255,0.1)' }}
        >
          <Filter size={18} />
        </IconButton>
        {showFilters && (
          <FormGroup row>
            {ALL_NODE_CLASSES.map((cls) => (
              <FormControlLabel
                key={cls}
                control={
                  <Checkbox
                    checked={visibleClasses.includes(cls)}
                    onChange={() => handleToggleClass(cls)}
                    size="small"
                    sx={{ p: 0.5 }}
                  />
                }
                label={
                  <Typography variant="caption" sx={{ textTransform: 'capitalize', fontSize: '0.7rem' }}>
                    {cls === 'vfact' ? 'ValFact' : cls === 'rfact' ? 'RelFact' : cls}
                  </Typography>
                }
                sx={{ mr: 1.5 }}
              />
            ))}
          </FormGroup>
        )}
      </Paper>

      <Paper
        elevation={2}
        sx={{
          position: 'absolute',
          top: 12,
          left: 12,
          p: 1.5,
          bgcolor: 'rgba(10, 10, 10, 0.85)',
          backdropFilter: 'blur(8px)',
          zIndex: 10,
          minWidth: 140,
        }}
      >
        <Typography
          variant="caption"
          sx={{ fontWeight: 600, color: 'text.secondary', display: 'block', mb: 1 }}
        >
          Nodes
        </Typography>
        {Object.entries(NODE_COLORS).map(([cls, color]) => (
          <Box key={cls} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Box
              sx={{ width: 10, height: 10, borderRadius: '50%', bgcolor: color, flexShrink: 0 }}
            />
            <Typography variant="caption" color="text.secondary">
              {NODE_CLASS_LABELS[cls]}
            </Typography>
          </Box>
        ))}

        <Typography
          variant="caption"
          sx={{ fontWeight: 600, color: 'text.secondary', display: 'block', mt: 1.5, mb: 1 }}
        >
          Edges
        </Typography>
        {Object.entries(EDGE_COLORS).map(([type, color]) => (
          <Box key={type} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.5 }}>
            <Box sx={{ width: 16, height: 3, bgcolor: color, flexShrink: 0 }} />
            <Typography variant="caption" color="text.secondary">
              {type}
            </Typography>
          </Box>
        ))}
      </Paper>
    </Box>
  );
});

export default GraphPanel;
