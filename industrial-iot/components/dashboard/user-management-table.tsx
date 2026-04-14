"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import type { UserRecord } from "@/types";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";

function UserDialog({
  triggerLabel,
  defaultUser,
}: {
  triggerLabel: string;
  defaultUser?: UserRecord;
}) {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant={defaultUser ? "ghost" : "secondary"} size="sm">
          {!defaultUser && <Plus className="mr-1 h-4 w-4" />}
          {triggerLabel}
        </Button>
      </DialogTrigger>
      <DialogContent>
        <h2 className="text-lg font-semibold text-white">
          {defaultUser ? "Edit User" : "Add User"}
        </h2>
        <div className="mt-4 space-y-3">
          <Input placeholder="Name" defaultValue={defaultUser?.name} />
          <Input placeholder="Email" defaultValue={defaultUser?.email} />
          <Input placeholder="Role" defaultValue={defaultUser?.role} />
          <Button className="w-full">Save Changes</Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export function UserManagementTable({ rows }: { rows: UserRecord[] }) {
  const [search, setSearch] = useState("");

  const filtered = rows.filter((row) =>
    `${row.name} ${row.email} ${row.role}`.toLowerCase().includes(search.toLowerCase()),
  );

  return (
    <Card>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-xl font-semibold text-white">Users & Roles</h1>
        <div className="flex gap-2">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            className="w-56"
            placeholder="Search user"
          />
          <UserDialog triggerLabel="Add User" />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-left text-slate-400">
              {["Name", "Email", "Role", "Last Login", "Access Level", "Status", "Action"].map(
                (head) => (
                  <th key={head} className="px-2 py-3">
                    {head}
                  </th>
                ),
              )}
            </tr>
          </thead>
          <tbody>
            {filtered.map((row) => (
              <tr key={row.id} className="border-b border-slate-900/80 hover:bg-slate-900/50">
                <td className="px-2 py-3 text-slate-200">{row.name}</td>
                <td className="px-2 py-3 text-slate-300">{row.email}</td>
                <td className="px-2 py-3 text-slate-300">{row.role}</td>
                <td className="px-2 py-3 text-slate-300">{row.lastLogin}</td>
                <td className="px-2 py-3 text-slate-300">{row.accessLevel}</td>
                <td className="px-2 py-3">
                  <Badge
                    className={
                      row.status === "Active"
                        ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-300"
                        : row.status === "Invited"
                          ? "border-amber-500/40 bg-amber-500/15 text-amber-300"
                          : "border-red-500/40 bg-red-500/15 text-red-300"
                    }
                  >
                    {row.status}
                  </Badge>
                </td>
                <td className="px-2 py-3">
                  <UserDialog triggerLabel="Edit" defaultUser={row} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
