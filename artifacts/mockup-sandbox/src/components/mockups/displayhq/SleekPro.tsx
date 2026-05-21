import React, { useState } from 'react';
import { 
  Monitor, 
  Wifi, 
  WifiOff, 
  Activity, 
  Clock, 
  Play, 
  MoreHorizontal, 
  Settings, 
  LayoutDashboard, 
  Layers, 
  Search, 
  Bell,
  Command,
  ChevronDown,
  RefreshCw,
  Terminal
} from 'lucide-react';

// Made-up data for the mockup
const STATS = [
  { label: 'Active Displays', value: '24', total: '/ 26', trend: '+2 this week', status: 'healthy' },
  { label: 'Network Sync', value: '99.9%', total: '', trend: 'Optimal', status: 'healthy' },
  { label: 'Bandwidth Usage', value: '1.2', total: 'TB', trend: '-0.4% vs last month', status: 'neutral' },
  { label: 'Critical Alerts', value: '1', total: '', trend: 'Action required', status: 'warning' },
];

const DEVICES = [
  { id: 'dev-01', name: 'Lobby Primary', location: 'HQ - Floor 1', status: 'online', playlist: 'Morning Corporate Loop', uptime: '99.9%', ip: '10.0.1.101', lastSync: '2m ago' },
  { id: 'dev-02', name: 'Conference A', location: 'HQ - Floor 2', status: 'online', playlist: 'Meeting Room Idle', uptime: '99.9%', ip: '10.0.1.102', lastSync: '5m ago' },
  { id: 'dev-03', name: 'Breakroom', location: 'HQ - Floor 2', status: 'offline', playlist: 'Employee News Q3', uptime: '84.2%', ip: '10.0.1.105', lastSync: '2h ago' },
  { id: 'dev-04', name: 'Executive Boardroom', location: 'HQ - Floor 5', status: 'online', playlist: 'Brand Anthem 4K', uptime: '100%', ip: '10.0.1.201', lastSync: 'Just now' },
  { id: 'dev-05', name: 'Cafeteria Menu L', location: 'Campus B', status: 'online', playlist: 'Lunch Menu - Tuesday', uptime: '98.4%', ip: '10.0.2.050', lastSync: '10m ago' },
  { id: 'dev-06', name: 'Cafeteria Menu R', location: 'Campus B', status: 'online', playlist: 'Lunch Menu - Tuesday', uptime: '98.5%', ip: '10.0.2.051', lastSync: '10m ago' },
];

const ACTIVITY = [
  { id: 1, type: 'alert', message: 'Breakroom display disconnected from network.', time: '2 hours ago' },
  { id: 2, type: 'update', message: 'Playlist "Lunch Menu - Tuesday" pushed to 2 devices.', time: '3 hours ago' },
  { id: 3, type: 'system', message: 'System OTA update v2.4.1 completed successfully.', time: 'Yesterday, 11:30 PM' },
  { id: 4, type: 'update', message: 'Playlist "Morning Corporate Loop" updated by Sarah M.', time: 'Yesterday, 4:15 PM' },
  { id: 5, type: 'status', message: 'Lobby Primary recovered from power loss.', time: 'Oct 24, 08:00 AM' },
];

export function SleekPro() {
  const [searchFocused, setSearchFocused] = useState(false);

  return (
    <div className="min-h-screen bg-[#000000] text-[#ededed] font-sans selection:bg-[#333] selection:text-white pb-20">
      <style dangerouslySetInnerHTML={{ __html: `
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');
        .sleek-font { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
        .mono-font { font-family: 'JetBrains Mono', monospace; }
        .glass-panel { background: rgba(10, 10, 10, 0.6); backdrop-filter: blur(12px); border-bottom: 1px solid #1f1f1f; }
        .hover-card { transition: all 0.2s ease; }
        .hover-card:hover { border-color: #333; background-color: #111; }
      `}} />
      
      <div className="sleek-font">
        {/* Top Navigation */}
        <nav className="glass-panel sticky top-0 z-50 h-14 flex items-center justify-between px-6">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2 text-white font-medium">
              <div className="w-6 h-6 bg-white text-black rounded flex items-center justify-center">
                <Command size={14} strokeWidth={3} />
              </div>
              DisplayHQ
            </div>
            
            <div className="hidden md:flex items-center gap-6 text-sm text-[#888]">
              <a href="#" className="text-white transition-colors">Overview</a>
              <a href="#" className="hover:text-white transition-colors">Devices</a>
              <a href="#" className="hover:text-white transition-colors">Playlists</a>
              <a href="#" className="hover:text-white transition-colors">Schedules</a>
              <a href="#" className="hover:text-white transition-colors">Settings</a>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-md border transition-colors ${searchFocused ? 'border-[#444] bg-[#111]' : 'border-[#1f1f1f] bg-transparent'}`}>
              <Search size={14} className="text-[#666]" />
              <input 
                type="text" 
                placeholder="Search..." 
                className="bg-transparent border-none outline-none text-sm w-48 text-[#ededed] placeholder-[#666]"
                onFocus={() => setSearchFocused(true)}
                onBlur={() => setSearchFocused(false)}
              />
              <div className="flex items-center gap-1 text-[10px] text-[#666] font-medium tracking-wider">
                <kbd className="bg-[#1f1f1f] px-1.5 py-0.5 rounded">⌘</kbd>
                <kbd className="bg-[#1f1f1f] px-1.5 py-0.5 rounded">K</kbd>
              </div>
            </div>
            
            <button className="text-[#888] hover:text-white transition-colors relative">
              <Bell size={18} />
              <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full border border-black"></span>
            </button>
            
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-zinc-700 to-zinc-500 border border-[#333] cursor-pointer"></div>
          </div>
        </nav>

        <main className="max-w-[1440px] mx-auto px-6 py-8">
          {/* Header Section */}
          <div className="flex items-end justify-between mb-8">
            <div>
              <h1 className="text-2xl font-semibold text-white tracking-tight mb-1">Network Overview</h1>
              <p className="text-sm text-[#888]">Monitoring 26 displays across 4 locations.</p>
            </div>
            <div className="flex items-center gap-3">
              <button className="px-3 py-1.5 rounded-md bg-white text-black text-sm font-medium hover:bg-zinc-200 transition-colors flex items-center gap-2">
                <Monitor size={14} />
                Add Device
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            {STATS.map((stat, i) => (
              <div key={i} className="border border-[#1f1f1f] bg-[#0a0a0a] rounded-lg p-5 flex flex-col justify-between hover-card">
                <div className="text-sm text-[#888] mb-3">{stat.label}</div>
                <div className="flex items-baseline gap-1 mb-2">
                  <span className="text-3xl font-semibold text-white tracking-tight">{stat.value}</span>
                  <span className="text-sm text-[#666] font-medium">{stat.total}</span>
                </div>
                <div className="flex items-center gap-2 text-xs">
                  {stat.status === 'healthy' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>}
                  {stat.status === 'warning' && <span className="w-1.5 h-1.5 rounded-full bg-red-500"></span>}
                  {stat.status === 'neutral' && <span className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>}
                  <span className="text-[#888]">{stat.trend}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Main Layout Grid */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            
            {/* Devices List (takes up 2 columns) */}
            <div className="xl:col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-white flex items-center gap-2">
                  <Monitor size={14} className="text-[#888]" />
                  Displays
                </h2>
                <button className="text-xs text-[#888] hover:text-white transition-colors flex items-center gap-1">
                  View all <ChevronDown size={12} className="-rotate-90" />
                </button>
              </div>
              
              <div className="border border-[#1f1f1f] bg-[#0a0a0a] rounded-lg overflow-hidden">
                <table className="w-full text-sm text-left">
                  <thead className="bg-[#111] text-[#666] border-b border-[#1f1f1f]">
                    <tr>
                      <th className="font-medium px-4 py-3 w-1/3">Device</th>
                      <th className="font-medium px-4 py-3 w-1/4">Status</th>
                      <th className="font-medium px-4 py-3 w-1/4">Current Playlist</th>
                      <th className="font-medium px-4 py-3 text-right">Last Sync</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[#1f1f1f]">
                    {DEVICES.map((device) => (
                      <tr key={device.id} className="hover:bg-[#111] transition-colors group">
                        <td className="px-4 py-3">
                          <div className="font-medium text-white">{device.name}</div>
                          <div className="text-xs text-[#666] mt-0.5">{device.location}</div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {device.status === 'online' ? (
                              <>
                                <Wifi size={14} className="text-emerald-500" />
                                <span className="text-[#888]">Online</span>
                              </>
                            ) : (
                              <>
                                <WifiOff size={14} className="text-red-500" />
                                <span className="text-[#888]">Offline</span>
                              </>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2 text-[#888]">
                            <Play size={12} className={device.status === 'online' ? 'text-blue-500' : 'text-[#444]'} />
                            <span className="truncate max-w-[150px]">{device.playlist}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="mono-font text-xs text-[#888]">{device.lastSync}</div>
                          <div className="opacity-0 group-hover:opacity-100 transition-opacity mt-1 flex justify-end gap-2">
                            <button className="text-[#666] hover:text-white"><RefreshCw size={12} /></button>
                            <button className="text-[#666] hover:text-white"><Terminal size={12} /></button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Activity Sidebar */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-medium text-white flex items-center gap-2">
                  <Activity size={14} className="text-[#888]" />
                  Activity Log
                </h2>
                <button className="text-xs text-[#888] hover:text-white transition-colors">
                  Filter
                </button>
              </div>
              
              <div className="border border-[#1f1f1f] bg-[#0a0a0a] rounded-lg p-1">
                {ACTIVITY.map((item, index) => (
                  <div key={item.id} className={`p-3 flex gap-3 text-sm ${index !== ACTIVITY.length - 1 ? 'border-b border-[#1f1f1f]/50' : ''}`}>
                    <div className="mt-0.5 shrink-0">
                      {item.type === 'alert' && <div className="w-2 h-2 rounded-full bg-red-500 mt-1.5" />}
                      {item.type === 'update' && <div className="w-2 h-2 rounded-full bg-blue-500 mt-1.5" />}
                      {item.type === 'system' && <div className="w-2 h-2 rounded-full bg-zinc-500 mt-1.5" />}
                      {item.type === 'status' && <div className="w-2 h-2 rounded-full bg-emerald-500 mt-1.5" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-[#ededed] mb-1 leading-snug">{item.message}</p>
                      <p className="text-xs text-[#666] mono-font">{item.time}</p>
                    </div>
                  </div>
                ))}
                <div className="p-2 pt-0 mt-2">
                  <button className="w-full py-2 text-xs font-medium text-[#888] bg-[#111] hover:bg-[#1a1a1a] rounded transition-colors border border-[#1f1f1f]">
                    View Complete Log
                  </button>
                </div>
              </div>
              
              {/* Quick Actions */}
              <div className="mt-6 border border-[#1f1f1f] bg-gradient-to-b from-[#111] to-[#0a0a0a] rounded-lg p-4">
                 <h3 className="text-xs font-semibold text-[#666] uppercase tracking-wider mb-3">Quick Actions</h3>
                 <div className="space-y-2">
                   <button className="w-full flex items-center justify-between p-2 rounded hover:bg-[#1f1f1f] transition-colors text-sm text-[#ededed]">
                     <span className="flex items-center gap-2"><RefreshCw size={14} className="text-[#888]" /> Sync All Devices</span>
                     <kbd className="mono-font text-[10px] text-[#666] bg-[#111] border border-[#222] px-1 rounded">⇧⌘S</kbd>
                   </button>
                   <button className="w-full flex items-center justify-between p-2 rounded hover:bg-[#1f1f1f] transition-colors text-sm text-[#ededed]">
                     <span className="flex items-center gap-2"><Play size={14} className="text-[#888]" /> Override Global Playlist</span>
                     <kbd className="mono-font text-[10px] text-[#666] bg-[#111] border border-[#222] px-1 rounded">⇧⌘P</kbd>
                   </button>
                 </div>
              </div>
            </div>

          </div>
        </main>
      </div>
    </div>
  );
}
