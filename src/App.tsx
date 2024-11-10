import './App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import MapPage from './pages/mapPage/MapPage';
// import Test from './pages/test';

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="*" element={<MapPage />} />
          {/* <Route path="/economicData" element={<EconomicDataPage />} /> */}
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;
