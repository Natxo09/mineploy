"use client";

import { AuthGuard } from "@/components/auth/auth-guard";
import { AppSidebar } from "@/components/sidebar/app-sidebar";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { Separator } from "@/components/ui/separator";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { usePathname, useParams } from "next/navigation";
import { useServer } from "@/hooks/use-servers";
import Link from "next/link";

export default function ServersLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const params = useParams();
  const serverId = params.id ? parseInt(params.id as string) : null;

  // Fetch server data if we're on a server detail page
  const { data: server } = useServer(serverId!, {
    enabled: !!serverId,
  });

  const isServerDetail = pathname.includes("/servers/") && serverId;

  return (
    <AuthGuard>
      <SidebarProvider>
        <AppSidebar />
        <SidebarInset>
          <header className="flex h-16 shrink-0 items-center gap-4 px-4">
            <SidebarTrigger className="-ml-1" />
            <Separator orientation="vertical" className="!h-4" />
            <Breadcrumb>
              <BreadcrumbList>
                <BreadcrumbItem>
                  {isServerDetail ? (
                    <BreadcrumbLink asChild>
                      <Link href="/servers">Servers</Link>
                    </BreadcrumbLink>
                  ) : (
                    <BreadcrumbPage>Servers</BreadcrumbPage>
                  )}
                </BreadcrumbItem>
                {isServerDetail && (
                  <>
                    <BreadcrumbSeparator />
                    <BreadcrumbItem>
                      <BreadcrumbPage>{server?.name || "Loading..."}</BreadcrumbPage>
                    </BreadcrumbItem>
                  </>
                )}
              </BreadcrumbList>
            </Breadcrumb>
          </header>
          <div className="flex flex-1 flex-col p-4 pt-0 overflow-auto">
            <div className="rounded-xl border-2 bg-background shadow-sm p-6 h-full flex flex-col gap-6">
              {children}
            </div>
          </div>
        </SidebarInset>
      </SidebarProvider>
    </AuthGuard>
  );
}
