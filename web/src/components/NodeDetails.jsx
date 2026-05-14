import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
} from '@mui/material';
import { MousePointerClick } from 'lucide-react';

const normalizeNodeClass = (cls) => {
  const map = {
    DDocument: 'document',
    DBlock: 'block',
    KEntity: 'entity',
    KValFact: 'vfact',
    KRelFact: 'rfact',
    document: 'document',
    block: 'block',
    entity: 'entity',
    vfact: 'vfact',
    rfact: 'rfact',
  };
  return map[cls] || cls;
};

const isKNodeInheritor = (cls) => {
  const normalized = normalizeNodeClass(cls);
  return ['entity', 'vfact', 'rfact'].includes(normalized);
};

const isEntity = (cls) => normalizeNodeClass(cls) === 'entity';
const isFact = (cls) => ['vfact', 'rfact'].includes(normalizeNodeClass(cls));

export default function NodeDetails({ node }) {
  if (!node) {
    return (
      <Paper
        elevation={0}
        sx={{
          height: '100%',
          borderRadius: 0,
          borderTop: 1,
          borderColor: 'rgba(255,255,255,0.05)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 1.5,
          bgcolor: 'background.paper',
        }}
      >
        <MousePointerClick size={32} color="#333333" />
        <Typography variant="body2" color="text.secondary">
          Click a node to see details
        </Typography>
      </Paper>
    );
  }

  const normalizedClass = normalizeNodeClass(node.node_class);

  let title;
  if (isEntity(node.node_class)) {
    title = `${node.type_code || 'KEntity'}: ${node.repr || node.uid}`;
  } else if (isFact(node.node_class)) {
    title = node.type_code || 'KFact';
  } else {
    title = node.name || node.repr || node.uid;
  }

  const renderCharacteristics = () => {
    if (!node.characteristics || Object.keys(node.characteristics).length === 0) {
      return null;
    }

    return (
      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
          Characteristics (Value Facts)
        </Typography>
        <TableContainer
          component={Box}
          sx={{
            bgcolor: 'background.default',
            borderRadius: 1,
            border: 1,
            borderColor: 'rgba(255,255,255,0.05)',
          }}
        >
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ fontWeight: 600, color: 'text.secondary', borderBottom: 1, borderColor: 'rgba(255,255,255,0.05)' }}>
                  Type
                </TableCell>
                <TableCell sx={{ fontWeight: 600, color: 'text.secondary', borderBottom: 1, borderColor: 'rgba(255,255,255,0.05)' }}>
                  Value
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(node.characteristics).map(([key, value]) => (
                <TableRow key={key}>
                  <TableCell sx={{ color: 'text.secondary', borderBottom: 1, borderColor: 'rgba(255,255,255,0.05)' }}>
                    {key}
                  </TableCell>
                  <TableCell sx={{ fontFamily: 'monospace', borderBottom: 1, borderColor: 'rgba(255,255,255,0.05)' }}>
                    {String(value)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    );
  };

  return (
    <Paper
      elevation={0}
      sx={{
        height: '100%',
        borderRadius: 0,
        borderTop: 1,
        borderColor: 'rgba(255,255,255,0.05)',
        overflow: 'auto',
        p: 2.5,
        bgcolor: 'background.paper',
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
        <Typography variant="h6" component="h3" sx={{ fontWeight: 600 }}>
          {title}
        </Typography>
        <Chip
          label={normalizedClass}
          size="small"
          sx={{
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            bgcolor: 'rgba(255,255,255,0.05)',
          }}
        />
      </Box>

      <Box sx={{ display: 'grid', gridTemplateColumns: isKNodeInheritor(node.node_class) ? '1fr 1fr' : '1fr', gap: 2, mb: 2 }}>
        <Box>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            UID
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'monospace',
              fontSize: '0.8rem',
              bgcolor: 'background.default',
              p: 1,
              borderRadius: 1,
              wordBreak: 'break-all',
            }}
          >
            {node.uid}
          </Typography>
        </Box>
        {isKNodeInheritor(node.node_class) && (
          <Box>
            <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
              Type
            </Typography>
            <Typography variant="body2">
              {node.type_code || 'N/A'}
            </Typography>
          </Box>
        )}
      </Box>

      {node.value !== undefined && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Value
          </Typography>
          <Typography
            variant="body2"
            sx={{
              fontFamily: 'monospace',
              bgcolor: 'background.default',
              p: 1.5,
              borderRadius: 1,
            }}
          >
            {String(node.value)}
          </Typography>
        </Box>
      )}

      {renderCharacteristics()}

      {node.mentions && node.mentions.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Mentions
          </Typography>
          <Typography variant="body2">
            {node.mentions.length} blocks
          </Typography>
        </Box>
      )}

      {node.objects && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
            Objects
          </Typography>
          <Typography variant="body2">
            {node.objects.length} connections
          </Typography>
        </Box>
      )}
    </Paper>
  );
}
