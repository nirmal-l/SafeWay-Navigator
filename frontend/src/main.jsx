import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import GuardianObserver from './components/GuardianObserver.jsx'

const path = window.location.pathname;
let componentToRender;

if (path.startsWith('/guardian/')) {
  const token = path.split('/guardian/')[1];
  componentToRender = <GuardianObserver token={token} />;
} else {
  componentToRender = <App />;
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {componentToRender}
  </StrictMode>,
)
