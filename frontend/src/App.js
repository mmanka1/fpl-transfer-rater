import './App.css';
import React from "react"
import {
  BrowserRouter as Router,
  Switch,
  Route
} from "react-router-dom";
import PortalView from './components/portalView'; 
import TeamView from './components/teamView'; 

function App() {
  return (
    <Router>
      <div className="App">
        <Switch>
          <Route exact path="/">
            <PortalView />
          </Route>
          <Route exact path="/team">
            <TeamView/>
          </Route>
        </Switch>
      </div>
    </Router>
  );
}

export default App;
