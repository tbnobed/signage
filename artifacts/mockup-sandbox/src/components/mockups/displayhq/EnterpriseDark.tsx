import React, { useState } from "react";
import { 
  Monitor, Server, AlertTriangle, CheckCircle, Activity, 
  Settings, LayoutDashboard, Layers, Users, LogOut, 
  Bell, Search, Menu, Filter, RefreshCw, XCircle, Clock, CheckCircle2, ChevronDown, Plus
} from "lucide-react";
import "./_group.css";

const MOCK_DEVICES = [
  { id: 1, name: "Lobby TV 1", status: "online", playlist: "Morning Promos", uptime: "14d 2h", ip: "192.168.1.101" },
  { id: 2, name: "Lobby TV 2", status: "online", playlist: "Brand Reel", uptime: "14d 2h", ip: "192.168.1.102" },
  { id: 3, name: "Conf Room A", status: "offline", playlist: "Screen Share", uptime: "Offline", ip: "192.168.1.105" },
  { id: 4, name: "Conf Room B", status: "online", playlist: "Dashboard View", uptime: "3d 14h", ip: "192.168.1.106" },
  { id: 5, name: "Breakroom", status: "error", playlist: "Holiday Content", uptime: "Error", ip: "192.168.1.110", errorMsg: "Media missing" },
  { id: 6, name: "Hallway North", status: "online", playlist: "Wayfinding", uptime: "34d 1h", ip: "192.168.2.40" },
  { id: 7, name: "Cafeteria Menu", status: "online", playlist: "Lunch Menu", uptime: "12d 5h", ip: "192.168.2.55" },
  { id: 8, name: "Exec Boardroom", status: "offline", playlist: "Standby", uptime: "Offline", ip: "192.168.1.200" },
];

const MOCK_ACTIVITIES = [
  { id: 1, type: "error", msg: "Breakroom TV failed to download media: holiday_bg.mp4", time: "2 min ago" },
  { id: 2, type: "info", msg: "Playlist 'Lunch Menu' updated by Admin", time: "14 min ago" },
  { id: 3, type: "offline", msg: "Conf Room A disconnected unexpectedly", time: "1 hr ago" },
  { id: 4, type: "online", msg: "Lobby TV 1 reconnected", time: "2 hrs ago" },
  { id: 5, type: "online", msg: "Lobby TV 2 reconnected", time: "2 hrs ago" },
  { id: 6, type: "info", msg: "System backup completed successfully", time: "4 hrs ago" },
  { id: 7, type: "offline", msg: "Exec Boardroom triggered auto-standby", time: "5 hrs ago" },
  { id: 8, type: "info", msg: "Firmware v2.4.1 deployed to 4 devices", time: "1 day ago" },
];

export function EnterpriseDark() {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <div className="enterprise-dark-theme min-h-[100dvh] w-full flex bg-[hsl(var(--background))] text-[hsl(var(--foreground))] overflow-hidden font-sans selection:bg-indigo-500/30">
      
      {/* Sidebar */}
      <aside className={`border-r border-[hsl(var(--border))] bg-[#0A0A0E] flex flex-col transition-all duration-300 z-20 relative ${sidebarOpen ? 'w-64' : 'w-20'}`}>
        <div className="h-16 flex items-center justify-between px-4 border-b border-[hsl(var(--border))]">
          <div className={`flex items-center gap-2 overflow-hidden ${!sidebarOpen && 'justify-center w-full'}`}>
            <div className="w-8 h-8 rounded bg-indigo-600 flex items-center justify-center glow-indigo shrink-0">
              <Monitor className="w-5 h-5 text-white" />
            </div>
            {sidebarOpen && <span className="font-bold text-lg tracking-tight whitespace-nowrap">DisplayHQ</span>}
          </div>
        </div>

        <nav className="flex-1 overflow-y-auto scrollbar-none py-4 px-2 space-y-1">
          <NavItem icon={<LayoutDashboard />} label="Dashboard" active open={sidebarOpen} />
          <NavItem icon={<Monitor />} label="Devices" badge="8" open={sidebarOpen} />
          <NavItem icon={<Layers />} label="Playlists" open={sidebarOpen} />
          <NavItem icon={<Server />} label="Network" open={sidebarOpen} />
          <NavItem icon={<Activity />} label="Analytics" open={sidebarOpen} />
          <div className="pt-4 mt-4 border-t border-[hsl(var(--border))]">
            <NavItem icon={<Users />} label="Team" open={sidebarOpen} />
            <NavItem icon={<Settings />} label="Settings" open={sidebarOpen} />
          </div>
        </nav>

        <div className="p-4 border-t border-[hsl(var(--border))]">
          <button 
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="flex items-center gap-3 w-full p-2 rounded-md hover:bg-[hsl(var(--muted))] transition-colors text-sm text-[hsl(var(--muted-foreground))]"
          >
            <Menu className="w-5 h-5 shrink-0" />
            {sidebarOpen && <span>Collapse Menu</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 bg-[#0d0e12] relative z-10">
        
        {/* Header */}
        <header className="h-16 border-b border-[hsl(var(--border))] flex items-center justify-between px-6 bg-[#0A0A0E]/80 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold tracking-tight text-white">Network Overview</h1>
            <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-[hsl(var(--muted))] border border-[hsl(var(--border))] text-sm text-[hsl(var(--muted-foreground))]">
              <span className="w-2 h-2 rounded-full bg-emerald-500 status-pulse-online"></span>
              All systems operational
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative hidden lg:block">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input 
                type="text" 
                placeholder="Search devices, playlists..." 
                className="pl-9 pr-4 py-1.5 bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-indigo-500 w-64 text-white"
              />
            </div>
            <button className="relative p-2 rounded-md hover:bg-[hsl(var(--muted))] text-gray-400 hover:text-white transition-colors">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-indigo-500 glow-indigo"></span>
            </button>
            <div className="w-8 h-8 rounded-full bg-indigo-900 border border-indigo-500/30 flex items-center justify-center text-indigo-200 font-medium text-sm">
              OP
            </div>
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-auto flex">
          
          <div className="flex-1 p-6 flex flex-col gap-6 min-w-0">
            {/* Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard title="Total Devices" value="8" trend="+2 this week" icon={<Monitor className="text-indigo-400" />} />
              <StatCard title="Online" value="5" subValue="62.5%" icon={<CheckCircle2 className="text-emerald-400" />} glow="glow-emerald" />
              <StatCard title="Offline" value="2" subValue="25.0%" icon={<Clock className="text-gray-400" />} />
              <StatCard title="Alerts" value="1" subValue="Requires attention" icon={<AlertTriangle className="text-red-400" />} glow="glow-red" />
            </div>

            {/* Devices Header */}
            <div className="flex items-center justify-between mt-4">
              <h2 className="text-lg font-medium text-white flex items-center gap-2">
                Active Displays
                <span className="px-2 py-0.5 rounded-full bg-[hsl(var(--muted))] text-xs text-gray-400 font-mono">8 total</span>
              </h2>
              <div className="flex items-center gap-2">
                <button className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-[hsl(var(--card))] border border-[hsl(var(--border))] text-sm hover:bg-[hsl(var(--muted))] transition-colors">
                  <Filter className="w-4 h-4" /> Filter
                </button>
                <button className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-indigo-600 hover:bg-indigo-700 text-white text-sm transition-colors glow-indigo font-medium border border-indigo-500">
                  <Plus className="w-4 h-4" /> Add Device
                </button>
              </div>
            </div>

            {/* Device Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4 pb-6">
              {MOCK_DEVICES.map(device => (
                <DeviceCard key={device.id} device={device} />
              ))}
            </div>
          </div>

          {/* Right Sidebar - Activity Feed */}
          <aside className="w-80 border-l border-[hsl(var(--border))] bg-[#0A0A0E]/50 hidden 2xl:flex flex-col">
            <div className="p-4 border-b border-[hsl(var(--border))] flex items-center justify-between">
              <h3 className="font-medium text-white flex items-center gap-2">
                <Activity className="w-4 h-4 text-indigo-400" />
                Network Log
              </h3>
              <button className="p-1.5 rounded-md hover:bg-[hsl(var(--muted))] text-gray-400 transition-colors">
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {MOCK_ACTIVITIES.map(activity => (
                <div key={activity.id} className="relative pl-4">
                  {/* Timeline line */}
                  <div className="absolute left-[7px] top-6 bottom-[-24px] w-px bg-[hsl(var(--border))] last:hidden"></div>
                  
                  {/* Timeline dot */}
                  <div className={`absolute left-0 top-1.5 w-[15px] h-[15px] rounded-full border-2 border-[#0A0A0E] flex items-center justify-center
                    ${activity.type === 'error' ? 'bg-red-500' : 
                      activity.type === 'online' ? 'bg-emerald-500' : 
                      activity.type === 'offline' ? 'bg-gray-500' : 'bg-indigo-500'}
                  `}>
                  </div>

                  <div className="bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-md p-3 ml-2">
                    <p className="text-sm text-gray-200 leading-snug mb-1.5">{activity.msg}</p>
                    <span className="text-xs text-gray-500 font-mono">{activity.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </aside>

        </div>
      </main>
    </div>
  );
}

function NavItem({ icon, label, badge, active, open }: { icon: React.ReactNode, label: string, badge?: string, active?: boolean, open: boolean }) {
  return (
    <a href="#" className={`flex items-center gap-3 px-3 py-2.5 rounded-md transition-all group relative overflow-hidden
      ${active 
        ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' 
        : 'text-gray-400 hover:text-white hover:bg-[hsl(var(--muted))]'
      }`}
    >
      {active && <div className="absolute left-0 top-0 bottom-0 w-1 bg-indigo-500"></div>}
      <div className={`shrink-0 ${active ? 'text-indigo-400' : 'text-gray-400 group-hover:text-white'}`}>
        {React.cloneElement(icon as React.ReactElement, { className: 'w-5 h-5' })}
      </div>
      
      {open && (
        <span className={`font-medium text-sm whitespace-nowrap ${active ? 'text-indigo-300' : ''}`}>
          {label}
        </span>
      )}
      
      {open && badge && (
        <span className="ml-auto bg-indigo-500 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">
          {badge}
        </span>
      )}
    </a>
  );
}

function StatCard({ title, value, subValue, trend, icon, glow }: any) {
  return (
    <div className={`bg-[hsl(var(--card))] border border-[hsl(var(--border))] rounded-lg p-5 flex flex-col justify-between relative overflow-hidden ${glow ? 'shadow-lg' : ''}`}>
      <div className={`absolute -right-6 -top-6 w-24 h-24 bg-current opacity-[0.03] rounded-full blur-2xl ${glow}`}></div>
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        <div className="p-2 bg-[#1A1B23] rounded-md border border-[hsl(var(--border))]">
          {React.cloneElement(icon as React.ReactElement, { className: `w-4 h-4 ${icon.props.className}` })}
        </div>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-3xl font-bold text-white tracking-tight">{value}</span>
        {subValue && <span className="text-sm text-gray-400 font-mono">{subValue}</span>}
      </div>
      {trend && <span className="text-xs text-emerald-400 mt-2 font-medium">{trend}</span>}
    </div>
  );
}

function DeviceCard({ device }: { device: any }) {
  const isOnline = device.status === 'online';
  const isError = device.status === 'error';
  const isOffline = device.status === 'offline';

  return (
    <div className={`bg-[hsl(var(--card))] border rounded-lg overflow-hidden flex flex-col group transition-all duration-200 hover:border-indigo-500/50 hover:shadow-[0_0_15px_-5px_rgba(99,102,241,0.2)]
      ${isError ? 'border-red-500/30' : 'border-[hsl(var(--border))]'}
    `}>
      {/* Screen representation */}
      <div className="h-32 bg-[#050508] relative border-b border-[hsl(var(--border))] flex items-center justify-center overflow-hidden">
        {/* Abstract content playing */}
        {isOnline && (
          <div className="absolute inset-0 opacity-20 bg-gradient-to-br from-indigo-900 via-purple-900 to-black mix-blend-screen animate-pulse duration-[3000ms]"></div>
        )}
        {isError && (
          <div className="absolute inset-0 bg-red-950/20 flex flex-col items-center justify-center">
            <AlertTriangle className="w-8 h-8 text-red-500 mb-2 opacity-50" />
            <span className="text-xs text-red-400 font-mono">{device.errorMsg}</span>
          </div>
        )}
        {isOffline && (
          <div className="absolute inset-0 bg-[#0A0A0E] flex items-center justify-center">
            <span className="text-xs text-gray-600 font-mono tracking-widest uppercase">No Signal</span>
          </div>
        )}
        
        {/* Status indicator overlay */}
        <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-black/60 backdrop-blur-sm px-2 py-1 rounded-md border border-white/5">
          <span className={`w-2 h-2 rounded-full 
            ${isOnline ? 'bg-emerald-500 status-pulse-online' : 
              isError ? 'bg-red-500 status-pulse-error' : 'bg-gray-500'}
          `}></span>
          <span className="text-[10px] font-bold tracking-wider text-white uppercase">{device.status}</span>
        </div>
      </div>

      {/* Info section */}
      <div className="p-4 flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-1">
          <h4 className="font-semibold text-white group-hover:text-indigo-300 transition-colors">{device.name}</h4>
          <button className="text-gray-500 hover:text-white transition-colors">
            <Settings className="w-4 h-4" />
          </button>
        </div>
        
        <div className="flex items-center gap-2 mb-4">
          <span className="text-xs text-gray-400 font-mono">{device.ip}</span>
        </div>

        <div className="mt-auto space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Playing</span>
            <span className={`font-medium truncate max-w-[120px] ${isOffline ? 'text-gray-600' : 'text-indigo-200'}`}>
              {device.playlist}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-500">Uptime</span>
            <span className="text-gray-300 font-mono text-xs">{device.uptime}</span>
          </div>
        </div>
      </div>
      
      {/* Action Footer */}
      <div className="border-t border-[hsl(var(--border))] bg-[#0A0A0E]/30 p-2 flex gap-2">
        <button className="flex-1 py-1.5 text-xs font-medium text-gray-300 hover:text-white hover:bg-[hsl(var(--muted))] rounded transition-colors flex items-center justify-center gap-1.5">
          <RefreshCw className="w-3 h-3" /> Restart
        </button>
        <button className="flex-1 py-1.5 text-xs font-medium text-gray-300 hover:text-white hover:bg-[hsl(var(--muted))] rounded transition-colors flex items-center justify-center gap-1.5">
          <Layers className="w-3 h-3" /> Change Content
        </button>
      </div>
    </div>
  );
}
