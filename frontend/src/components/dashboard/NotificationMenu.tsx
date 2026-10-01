import { useEffect, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { getApiErrorMessage } from "@/lib/api";
import {
  getNotifications,
  getUnreadNotificationCount,
  markNotificationAsRead,
  type NotificationRecord,
} from "@/services/notifications";

function formatNotificationDate(value: string): string {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "" : date.toLocaleString();
}

export default function NotificationMenu() {
  const navigate = useNavigate();
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationRecord[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    getUnreadNotificationCount()
      .then((count) => {
        if (active) setUnreadCount(count);
      })
      .catch((countError: unknown) => {
        if (active) {
          setError(
            getApiErrorMessage(
              countError,
              "Unable to load notification count."
            )
          );
        }
      });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!isOpen) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  async function loadNotifications() {
    setLoading(true);
    setError(null);
    try {
      const result = await getNotifications();
      setNotifications(result.notifications);
      setUnreadCount(result.unread_count);
    } catch (loadError) {
      setError(
        getApiErrorMessage(loadError, "Unable to load notifications.")
      );
    } finally {
      setLoading(false);
    }
  }

  function togglePanel() {
    const opening = !isOpen;
    setIsOpen(opening);
    if (opening) void loadNotifications();
  }

  async function handleNotificationClick(
    notification: NotificationRecord
  ) {
    if (!notification.is_read) {
      try {
        await markNotificationAsRead(notification.id);
        setNotifications((current) =>
          current.map((item) =>
            item.id === notification.id ? { ...item, is_read: true } : item
          )
        );
        setUnreadCount((count) => Math.max(0, count - 1));
      } catch (markError) {
        setError(
          getApiErrorMessage(markError, "Unable to mark notification as read.")
        );
        return;
      }
    }

    setIsOpen(false);
    if (
      notification.action_url?.startsWith("/") &&
      !notification.action_url.startsWith("//")
    ) {
      navigate(notification.action_url);
    }
  }

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        aria-label={
          unreadCount > 0
            ? `Notifications, ${unreadCount} unread`
            : "Notifications"
        }
        aria-expanded={isOpen}
        aria-controls="notification-panel"
        onClick={togglePanel}
        className="relative rounded-lg p-2 transition hover:bg-accent"
      >
        <Bell size={21} aria-hidden="true" />
        {unreadCount > 0 && (
          <span className="absolute right-1 top-1 min-h-2 min-w-2 rounded-full bg-red-500" />
        )}
      </button>

      {isOpen && (
        <>
          <div
            aria-hidden="true"
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <section
            id="notification-panel"
            aria-label="Notifications"
            className="fixed right-3 top-20 z-50 flex max-h-[calc(100dvh-6rem)] w-[min(24rem,calc(100vw-1.5rem))] flex-col overflow-hidden rounded-xl border border-border bg-card shadow-xl sm:right-4"
          >
            <header className="flex items-center justify-between border-b border-border px-4 py-3">
              <h2 className="font-semibold text-foreground">Notifications</h2>
              {unreadCount > 0 && (
                <span className="text-xs text-muted-foreground">
                  {unreadCount} unread
                </span>
              )}
            </header>

            {error && (
              <div role="alert" className="border-b border-border px-4 py-3">
                <p className="text-sm text-destructive">{error}</p>
                <button
                  type="button"
                  onClick={() => void loadNotifications()}
                  className="mt-2 rounded-lg bg-secondary px-3 py-1.5 text-sm font-medium text-secondary-foreground"
                >
                  Retry
                </button>
              </div>
            )}

            <div className="min-h-0 overflow-y-auto overscroll-contain">
              {loading ? (
                <p role="status" className="px-4 py-6 text-sm text-muted-foreground">
                  Loading notifications...
                </p>
              ) : notifications.length === 0 ? (
                !error && (
                  <p className="px-4 py-6 text-sm text-muted-foreground">
                    You have no notifications.
                  </p>
                )
              ) : (
                <ul className="divide-y divide-border">
                  {notifications.map((notification) => {
                    const createdAt = formatNotificationDate(
                      notification.created_at
                    );

                    return (
                      <li key={notification.id}>
                        <button
                          type="button"
                          onClick={() =>
                            void handleNotificationClick(notification)
                          }
                          className={`w-full px-4 py-3 text-left transition hover:bg-accent ${
                            notification.is_read ? "" : "bg-primary/5"
                          }`}
                        >
                          <span className="flex items-start gap-2">
                            {!notification.is_read && (
                              <span
                                aria-label="Unread"
                                className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-primary"
                              />
                            )}
                            <span className="min-w-0 flex-1">
                              <span className="block break-words text-sm font-semibold text-foreground">
                                {notification.title}
                              </span>
                              <span className="mt-1 block break-words text-sm text-muted-foreground">
                                {notification.message}
                              </span>
                              {createdAt && (
                                <time
                                  dateTime={notification.created_at}
                                  className="mt-2 block text-xs text-muted-foreground"
                                >
                                  {createdAt}
                                </time>
                              )}
                            </span>
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          </section>
        </>
      )}
    </>
  );
}
