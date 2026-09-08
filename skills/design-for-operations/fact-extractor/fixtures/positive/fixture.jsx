// React written in JavaScript, not TypeScript. The outbound rule must cover both: a
// TypeScript-only rule read this file as having no calls at all.
import React from 'react';
import axios from 'axios';

export function Orders() {
  fetch('/api/orders');
  axios('/api/orders/legacy');
  axios.get('/api/orders/summary');
  const host = process.env.REACT_APP_API_HOST;
  return <div>{host}</div>;
}
