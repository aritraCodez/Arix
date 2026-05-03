import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './Dashboard/HomePage';
import Privacy from './Dashboard/Privacy';
import HowToUse from './Dashboard/HowToUse';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/privacy" element={<Privacy />} />
        <Route path="/how-to-use" element={<HowToUse />} />
      </Routes>
    </Router>
  );
}

export default App;
