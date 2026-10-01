import api from "@/lib/api";

export interface NotificationRecord {
  id: number;
  title: string;
  message: string;
  type: string;
  is_read: boolean;
  action_url: string | null;
  created_at: string;
}

export interface NotificationList {
  notifications: NotificationRecord[];
  total: number;
  unread_count: number;
}

export async function getNotifications(): Promise<NotificationList> {
  const response = await api.get<NotificationList>("/notifications");
  return response.data;
}

export async function getUnreadNotificationCount(): Promise<number> {
  const response = await api.get<{ unread_count: number }>(
    "/notifications/unread-count"
  );
  return response.data.unread_count;
}

export async function markNotificationAsRead(
  notificationId: number
): Promise<void> {
  await api.put(`/notifications/${notificationId}/read`);
}
