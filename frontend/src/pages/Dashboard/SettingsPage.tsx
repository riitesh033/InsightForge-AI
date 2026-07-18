import { useState } from "react";
import {
  User,
  Lock,
  Bell,
  Moon,
  Trash2,
  Save,
} from "lucide-react";

export default function SettingsPage() {
  const [name, setName] = useState("John Doe");
  const [email, setEmail] = useState("john@example.com");

  return (
    <div className="space-y-8">

      {/* Header */}

      <div>

        <h1 className="text-3xl font-bold text-foreground">
          Settings
        </h1>

        <p className="mt-2 text-muted-foreground">
          Manage your account preferences and application settings.
        </p>

      </div>

      {/* Profile */}

      <div className="rounded-xl border border-border bg-card p-6">

        <div className="mb-6 flex items-center gap-3">

          <User className="text-primary" size={22} />

          <h2 className="text-xl font-semibold text-foreground">
            Profile
          </h2>

        </div>

        <div className="grid gap-6 md:grid-cols-2">

          <div>

            <label className="mb-2 block text-sm font-medium text-foreground">
              Full Name
            </label>

            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
            />

          </div>

          <div>

            <label className="mb-2 block text-sm font-medium text-foreground">
              Email
            </label>

            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
            />

          </div>

        </div>

      </div>

      {/* Security */}

      <div className="rounded-xl border border-border bg-card p-6">

        <div className="mb-6 flex items-center gap-3">

          <Lock className="text-primary" size={22} />

          <h2 className="text-xl font-semibold text-foreground">
            Security
          </h2>

        </div>

        <div className="space-y-4">

          <input
            type="password"
            placeholder="Current Password"
            className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
          />

          <input
            type="password"
            placeholder="New Password"
            className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
          />

          <input
            type="password"
            placeholder="Confirm Password"
            className="w-full rounded-lg border border-border bg-background p-3 text-foreground focus:border-primary focus:outline-none"
          />

        </div>

      </div>

      {/* Preferences */}

      <div className="rounded-xl border border-border bg-card p-6">

        <div className="mb-6 flex items-center gap-3">

          <Bell className="text-primary" size={22} />

          <h2 className="text-xl font-semibold text-foreground">
            Notifications
          </h2>

        </div>

        <div className="space-y-4">

          <label className="flex items-center justify-between">

            <span className="text-foreground">
              Email Notifications
            </span>

            <input type="checkbox" defaultChecked />

          </label>

          <label className="flex items-center justify-between">

            <span className="text-foreground">
              Dataset Processing Alerts
            </span>

            <input type="checkbox" defaultChecked />

          </label>

          <label className="flex items-center justify-between">

            <span className="text-foreground">
              Weekly Reports
            </span>

            <input type="checkbox" />

          </label>

        </div>

      </div>

      {/* Appearance */}

      <div className="rounded-xl border border-border bg-card p-6">

        <div className="mb-6 flex items-center gap-3">

          <Moon className="text-primary" size={22} />

          <h2 className="text-xl font-semibold text-foreground">
            Appearance
          </h2>

        </div>

        <p className="text-muted-foreground">
          Use the theme toggle in the top-right corner to switch
          between Light and Dark mode.
        </p>

      </div>

      {/* Save */}

      <div className="flex justify-end">

        <button
          className="
            flex
            items-center
            gap-2
            rounded-lg
            bg-primary
            px-6
            py-3
            text-primary-foreground
            transition
            hover:opacity-90
          "
        >

          <Save size={18} />

          Save Changes

        </button>

      </div>

      {/* Danger Zone */}

      <div className="rounded-xl border border-red-500 bg-card p-6">

        <div className="mb-4 flex items-center gap-3">

          <Trash2
            className="text-red-500"
            size={22}
          />

          <h2 className="text-xl font-semibold text-red-500">
            Danger Zone
          </h2>

        </div>

        <p className="mb-5 text-muted-foreground">
          Deleting your account will permanently remove all
          datasets, reports, chats and settings.
        </p>

        <button
          className="
            rounded-lg
            bg-red-600
            px-6
            py-3
            text-white
            transition
            hover:bg-red-700
          "
        >
          Delete Account
        </button>

      </div>

    </div>
  );
}