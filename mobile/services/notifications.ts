import api from './api';

export const getNotifications = (unread?: boolean) =>
  api.get('/notifications', { params: { unread } });

export const markRead = (id: string) =>
  api.put(`/notifications/${id}/read`);
