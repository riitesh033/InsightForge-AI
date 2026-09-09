import { useState, useEffect } from "react";
import {
  User,
  Lock,
  Bell,
  Moon,
  Trash2,
  Save,
  Upload,
  X,
  Image as ImageIcon,
} from "lucide-react";

import { useAuth } from "@/hooks/useAuth";
import { showSuccess, showError } from "@/lib/toast";
import {
  updateProfile,
  changePassword,
  uploadProfilePicture,
  removeProfilePicture,
  setBuiltinAvatar,
  deleteAccount,
} from "@/services/auth";

// Built-in avatar options
const BUILTIN_AVATARS = [
  "avatar_01",
  "avatar_02",
  "avatar_03",
  "avatar_04",
  "avatar_05",
  "avatar_06",
  "avatar_07",
  "avatar_08",
];

export default function SettingsPage() {
  const { user, updateUserProfile, logout, isAuthenticated } = useAuth();

  // Profile state
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  // Password state
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  // Profile picture state
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const [showAvatarSelector, setShowAvatarSelector] = useState(false);

  // Notification preferences
  const [emailNotifications, setEmailNotifications] = useState(true);
  const [datasetAlerts, setDatasetAlerts] = useState(true);
  const [weeklyReports, setWeeklyReports] = useState(false);

  // Delete account state
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);

  // Load user data on mount
  useEffect(() => {
    if (user) {
      setFullName(user.full_name);
      setEmail(user.email);
    }

    const savedEmailNotifs = localStorage.getItem("emailNotifications");
    const savedDatasetAlerts = localStorage.getItem("datasetAlerts");
    const savedWeeklyReports = localStorage.getItem("weeklyReports");

    if (savedEmailNotifs !== null) setEmailNotifications(JSON.parse(savedEmailNotifs));
    if (savedDatasetAlerts !== null) setDatasetAlerts(JSON.parse(savedDatasetAlerts));
    if (savedWeeklyReports !== null) setWeeklyReports(JSON.parse(savedWeeklyReports));
  }, [user]);

  // Get profile picture URL
  function getProfilePictureUrl() {
    if (!user?.profile_picture) return null;

    if (user.profile_picture.startsWith("builtin:")) {
      const avatarId = user.profile_picture.replace("builtin:", "");
      return `/avatars/${avatarId}.svg`;
    }

    return `${import.meta.env.VITE_API_BASE_URL || "/api/v1"}${user.profile_picture}`;
  }

  // Handle profile update
  async function handleSaveProfile() {
    if (!fullName.trim()) {
      showError("Full name is required.");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      showError("Please enter a valid email address.");
      return;
    }

    try {
      setIsSavingProfile(true);
      const updatedUser = await updateProfile(fullName, email);
      updateUserProfile(updatedUser);
      showSuccess("Profile updated successfully.");
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to update profile.";
      showError(message);
    } finally {
      setIsSavingProfile(false);
    }
  }

  // Handle password change
  async function handleChangePassword() {
    if (!currentPassword || !newPassword || !confirmPassword) {
      showError("All password fields are required.");
      return;
    }

    if (newPassword.length < 8) {
      showError("New password must be at least 8 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      showError("New passwords do not match.");
      return;
    }

    if (currentPassword === newPassword) {
      showError("New password must be different from current password.");
      return;
    }

    try {
      setIsChangingPassword(true);
      await changePassword(currentPassword, newPassword);
      showSuccess("Password changed successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to change password.";
      showError(message);
    } finally {
      setIsChangingPassword(false);
    }
  }

  // Handle profile picture upload
  async function handleUploadPicture(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];

    if (!file) return;

    const allowedTypes = ["image/jpeg", "image/jpg", "image/png", "image/webp"];
    if (!allowedTypes.includes(file.type)) {
      showError("Unsupported file type. Please upload JPG, PNG, or WEBP.");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      showError("File size must be less than 5MB.");
      return;
    }

    try {
      setIsUploadingImage(true);
      const updatedUser = await uploadProfilePicture(file);
      updateUserProfile(updatedUser);
      showSuccess("Profile picture updated successfully.");
      setShowAvatarSelector(false);
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to upload picture.";
      showError(message);
    } finally {
      setIsUploadingImage(false);
    }
  }

  // Handle built-in avatar selection
  async function handleSelectAvatar(avatarId: string) {
    try {
      const updatedUser = await setBuiltinAvatar(avatarId);
      updateUserProfile(updatedUser);
      showSuccess("Avatar selected successfully.");
      setShowAvatarSelector(false);
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to select avatar.";
      showError(message);
    }
  }

  // Handle remove picture
  async function handleRemovePicture() {
    try {
      const updatedUser = await removeProfilePicture();
      updateUserProfile(updatedUser);
      showSuccess("Profile picture removed.");
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to remove picture.";
      showError(message);
    }
  }

  // Handle notification preference changes
  function handleNotificationChange(type: string, value: boolean) {
    switch (type) {
      case "email":
        setEmailNotifications(value);
        localStorage.setItem("emailNotifications", JSON.stringify(value));
        break;
      case "dataset":
        setDatasetAlerts(value);
        localStorage.setItem("datasetAlerts", JSON.stringify(value));
        break;
      case "weekly":
        setWeeklyReports(value);
        localStorage.setItem("weeklyReports", JSON.stringify(value));
        break;
    }
  }

  // Handle account deletion
  async function handleDeleteAccount() {
    const confirmed = window.confirm(
      "Are you sure you want to delete your account? This action cannot be undone."
    );

    if (!confirmed) return;

    try {
      setIsDeletingAccount(true);
      await deleteAccount();
      logout();
      showSuccess("Account deleted successfully.");
    } catch (error: any) {
      const message = error?.response?.data?.detail || "Failed to delete account.";
      showError(message);
    } finally {
      setIsDeletingAccount(false);
    }
  }

  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center justify-center py-12">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-foreground">Settings</h1>
        <p className="mt-2 text-muted-foreground">
          Manage your account preferences and application settings.
        </p>
      </div>

      {/* Profile Section */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="mb-6 flex items-center gap-3">
          <User className="text-primary" size={22} />
          <h2 className="text-xl font-semibold text-foreground">Profile</h2>
        </div>

        {/* Profile Picture */}
        <div className="mb-6 flex items-center gap-6">
          <div className="relative h-24 w-24 overflow-hidden rounded-full bg-muted">
            {getProfilePictureUrl() ? (
              <img
                src={getProfilePictureUrl()!}
                alt="Profile"
                className="h-full w-full object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = "/avatars/avatar_01.svg";
                }}
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center bg-primary/10">
                <User className="h-12 w-12 text-primary" />
              </div>
            )}
          </div>

          <div className="flex gap-3">
            <label className="cursor-pointer">
              <input
                type="file"
                accept="image/*"
                onChange={handleUploadPicture}
                className="hidden"
                disabled={isUploadingImage}
              />
              <span className={`
                flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium
                ${isUploadingImage
                  ? "bg-muted text-muted-foreground cursor-not-allowed"
                  : "bg-primary text-primary-foreground hover:opacity-90"
                }
              `}>
                <Upload size={16} />
                {isUploadingImage ? "Uploading..." : "Upload Photo"}
              </span>
            </label>

            <button
              onClick={() => setShowAvatarSelector(!showAvatarSelector)}
              className="flex items-center gap-2 rounded-lg bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground hover:bg-secondary/80"
            >
              <ImageIcon size={16} />
              Choose Avatar
            </button>

            {user.profile_picture && (
              <button
                onClick={handleRemovePicture}
                className="flex items-center gap-2 rounded-lg bg-destructive/10 px-4 py-2 text-sm font-medium text-destructive hover:bg-destructive/20"
              >
                <X size={16} />
                Remove
              </button>
            )}
          </div>
        </div>

        {/* Avatar Selector */}
        {showAvatarSelector && (
          <div className="mb-6 rounded-lg border border-border bg-background p-4">
            <h3 className="mb-3 text-sm font-medium text-foreground">Choose a Built-in Avatar</h3>
            <div className="grid grid-cols-4 gap-3 sm:grid-cols-8">
              {BUILTIN_AVATARS.map((avatarId) => (
                <button
                  key={avatarId}
                  onClick={() => handleSelectAvatar(avatarId)}
                  className={`
                    relative aspect-square rounded-lg overflow-hidden border-2 transition
                    ${user?.profile_picture === `builtin:${avatarId}`
                      ? "border-primary"
                      : "border-transparent hover:border-muted"
                    }
                  `}
                >
                  <img
                    src={`/avatars/${avatarId}.svg`}
                    alt={avatarId}
                    className="h-full w-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLImageElement).src = "/avatars/avatar_01.svg";
                    }}
                  />
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Name and Email */}
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">Full Name</label>
            <input
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">Email</label>
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleSaveProfile}
            disabled={isSavingProfile}
            className={`
              flex items-center gap-2 rounded-lg px-6 py-3 font-medium text-primary-foreground transition
              ${isSavingProfile
                ? "bg-muted cursor-not-allowed"
                : "bg-primary hover:opacity-90"
              }
            `}
          >
            <Save size={18} />
            {isSavingProfile ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {/* Security Section */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="mb-6 flex items-center gap-3">
          <Lock className="text-primary" size={22} />
          <h2 className="text-xl font-semibold text-foreground">Security</h2>
        </div>

        <div className="space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">Current Password</label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              placeholder="Enter current password"
              className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">New Password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Enter new password"
              className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-foreground">Confirm New Password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm new password"
              className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
            />
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button
            onClick={handleChangePassword}
            disabled={isChangingPassword}
            className={`
              flex items-center gap-2 rounded-lg px-6 py-3 font-medium text-primary-foreground transition
              ${isChangingPassword
                ? "bg-muted cursor-not-allowed"
                : "bg-primary hover:opacity-90"
              }
            `}
          >
            <Lock size={18} />
            {isChangingPassword ? "Changing..." : "Change Password"}
          </button>
        </div>
      </div>

      {/* Notifications Section */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="mb-6 flex items-center gap-3">
          <Bell className="text-primary" size={22} />
          <h2 className="text-xl font-semibold text-foreground">Notifications</h2>
        </div>

        <div className="space-y-4">
          <label className="flex items-center justify-between">
            <span className="text-foreground">Email Notifications</span>
            <input
              type="checkbox"
              checked={emailNotifications}
              onChange={(e) => handleNotificationChange("email", e.target.checked)}
              className="h-5 w-5"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-foreground">Dataset Processing Alerts</span>
            <input
              type="checkbox"
              checked={datasetAlerts}
              onChange={(e) => handleNotificationChange("dataset", e.target.checked)}
              className="h-5 w-5"
            />
          </label>

          <label className="flex items-center justify-between">
            <span className="text-foreground">Weekly Reports</span>
            <input
              type="checkbox"
              checked={weeklyReports}
              onChange={(e) => handleNotificationChange("weekly", e.target.checked)}
              className="h-5 w-5"
            />
          </label>
        </div>
      </div>

      {/* Appearance Section */}
      <div className="rounded-xl border border-border bg-card p-6">
        <div className="mb-6 flex items-center gap-3">
          <Moon className="text-primary" size={22} />
          <h2 className="text-xl font-semibold text-foreground">Appearance</h2>
        </div>

        <p className="text-muted-foreground">
          Use the theme toggle in the top-right corner to switch between Light and Dark mode.
        </p>
      </div>

      {/* Danger Zone */}
      <div className="rounded-xl border border-red-500 bg-card p-6">
        <div className="mb-4 flex items-center gap-3">
          <Trash2 className="text-red-500" size={22} />
          <h2 className="text-xl font-semibold text-red-500">Danger Zone</h2>
        </div>

        <p className="mb-5 text-muted-foreground">
          Deleting your account will permanently remove all datasets, reports, chats and settings.
        </p>

        <button
          onClick={handleDeleteAccount}
          disabled={isDeletingAccount}
          className={`
            rounded-lg px-6 py-3 font-medium text-white transition
            ${isDeletingAccount
              ? "bg-muted cursor-not-allowed"
              : "bg-red-600 hover:bg-red-700"
            }
          `}
        >
          {isDeletingAccount ? "Deleting Account..." : "Delete Account"}
        </button>
      </div>

    </div>
  );
}
