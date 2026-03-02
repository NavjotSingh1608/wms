import api from './api';

export const getDispenseQueue = (itemCode: string) =>
  api.get(`/dispensing/queue/${itemCode}`);

export const dispense = (data: any) => api.post('/dispensing', data);
