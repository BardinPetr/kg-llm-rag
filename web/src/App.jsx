import { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Tabs,
  Tab,
} from '@mui/material';
import { Brain } from 'lucide-react';
import DocumentsTab from './components/DocumentsTab';
import SearchTab from './components/SearchTab';

function App() {
  const [activeTab, setActiveTab] = useState(1);
  const handleChange = (_event, newValue) => {
    setActiveTab(newValue);
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <AppBar position="static" elevation={0} sx={{ borderBottom: 1, borderColor: 'rgba(255,255,255,0.05)' }}>
        <Toolbar sx={{ minHeight: 56, px: 2 }}>
          <Tabs
            value={activeTab}
            onChange={handleChange}
            textColor="primary"
            indicatorColor="primary"
            sx={{ minHeight: 56 }}
          >
            <Tab label="Documents" sx={{ textTransform: 'none', fontWeight: 500, minHeight: 56 }} />
            <Tab label="Search" sx={{ textTransform: 'none', fontWeight: 500, minHeight: 56 }} />
          </Tabs>
        </Toolbar>
      </AppBar>

      <Box sx={{ flex: 1, overflow: 'hidden' }}>
        {activeTab === 0 && <DocumentsTab />}
        {activeTab === 1 && <SearchTab />}
      </Box>
    </Box>
  );
}

export default App;
