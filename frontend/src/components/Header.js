import React from 'react';
import './Header.css';

const Header = () => {
  return (
    <div className="header">
      <div className="header-logo">
        <img src={require("./logo/SLCC_Demo_v02.png")} alt="SLCC Demo Logo" />
        <span>251203 SLCC Agent UI Demo</span>
      </div>
    </div>
  );
};

export default Header;
