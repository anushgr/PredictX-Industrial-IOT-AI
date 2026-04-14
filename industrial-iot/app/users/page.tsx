import { users } from "@/lib/mock-data";
import { UserManagementTable } from "@/components/dashboard/user-management-table";

export default function UsersPage() {
  return <UserManagementTable rows={users} />;
}
