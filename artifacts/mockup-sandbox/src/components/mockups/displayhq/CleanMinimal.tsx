import React from 'react';
import { LayoutDashboard, MonitorPlay, Film, CalendarDays, Settings, Bell, Search, Plus, MoreHorizontal, CheckCircle2, AlertCircle, XCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Input } from '@/components/ui/input';

export function CleanMinimal() {
  return (
    <div className="min-h-screen bg-[#FAFAFA] text-[#111111] font-sans overflow-hidden flex flex-col">
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        .clean-minimal-dashboard {
          font-family: 'Inter', sans-serif;
        }
        .clean-shadow {
          box-shadow: 0 1px 2px rgba(0,0,0,0.02), 0 4px 12px rgba(0,0,0,0.03);
        }
        .clean-border {
          border: 1px solid rgba(0,0,0,0.06);
        }
      `}</style>
      
      {/* Top Navigation */}
      <header className="h-14 bg-white clean-border flex items-center justify-between px-6 sticky top-0 z-10">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-black rounded flex items-center justify-center text-white font-bold text-xs">
              D
            </div>
            <span className="font-semibold text-sm tracking-tight">DisplayHQ</span>
          </div>
          <nav className="hidden md:flex items-center gap-1 text-sm font-medium text-gray-500">
            <a href="#" className="px-3 py-1.5 rounded-md bg-gray-100 text-gray-900">Overview</a>
            <a href="#" className="px-3 py-1.5 rounded-md hover:bg-gray-50 hover:text-gray-900 transition-colors">Devices</a>
            <a href="#" className="px-3 py-1.5 rounded-md hover:bg-gray-50 hover:text-gray-900 transition-colors">Playlists</a>
            <a href="#" className="px-3 py-1.5 rounded-md hover:bg-gray-50 hover:text-gray-900 transition-colors">Media</a>
            <a href="#" className="px-3 py-1.5 rounded-md hover:bg-gray-50 hover:text-gray-900 transition-colors">Schedules</a>
          </nav>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="relative hidden md:block w-64">
            <Search className="absolute left-2.5 top-1.5 h-4 w-4 text-gray-400" />
            <Input 
              placeholder="Search displays, media..." 
              className="h-8 pl-9 bg-gray-50 border-transparent focus:bg-white focus:border-gray-200 text-xs shadow-none"
            />
          </div>
          <button className="text-gray-400 hover:text-gray-600">
            <Bell className="w-4 h-4" />
          </button>
          <Avatar className="h-7 w-7 border clean-border">
            <AvatarFallback className="bg-white text-xs text-gray-600">JD</AvatarFallback>
          </Avatar>
        </div>
      </header>

      <main className="flex-1 overflow-auto p-8 max-w-7xl mx-auto w-full clean-minimal-dashboard">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">Good morning, Julian</h1>
            <p className="text-sm text-gray-500 mt-1">Here's what's happening across your displays today.</p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" className="h-9 text-sm clean-border shadow-sm bg-white hover:bg-gray-50">
              <Settings className="w-4 h-4 mr-2" />
              Settings
            </Button>
            <Button className="h-9 text-sm bg-black hover:bg-gray-800 text-white shadow-sm">
              <Plus className="w-4 h-4 mr-2" />
              New Playlist
            </Button>
          </div>
        </div>

        {/* Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <Card className="clean-shadow clean-border rounded-xl bg-white border-0">
            <CardHeader className="p-5 pb-2 flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Displays</CardTitle>
              <MonitorPlay className="w-4 h-4 text-gray-400" />
            </CardHeader>
            <CardContent className="p-5 pt-0">
              <div className="text-3xl font-semibold">24</div>
              <div className="flex items-center mt-1 text-xs text-emerald-600 font-medium">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                <span>21 online</span>
              </div>
            </CardContent>
          </Card>
          <Card className="clean-shadow clean-border rounded-xl bg-white border-0">
            <CardHeader className="p-5 pb-2 flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-xs font-medium text-gray-500 uppercase tracking-wider">Active Playlists</CardTitle>
              <Film className="w-4 h-4 text-gray-400" />
            </CardHeader>
            <CardContent className="p-5 pt-0">
              <div className="text-3xl font-semibold">8</div>
              <div className="flex items-center mt-1 text-xs text-gray-500 font-medium">
                <span>3 scheduled later</span>
              </div>
            </CardContent>
          </Card>
          <Card className="clean-shadow clean-border rounded-xl bg-white border-0">
            <CardHeader className="p-5 pb-2 flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-xs font-medium text-gray-500 uppercase tracking-wider">Total Media</CardTitle>
              <LayoutDashboard className="w-4 h-4 text-gray-400" />
            </CardHeader>
            <CardContent className="p-5 pt-0">
              <div className="text-3xl font-semibold">142</div>
              <div className="flex items-center mt-1 text-xs text-gray-500 font-medium">
                <span>12 added this week</span>
              </div>
            </CardContent>
          </Card>
          <Card className="clean-shadow clean-border rounded-xl bg-white border-0">
            <CardHeader className="p-5 pb-2 flex flex-row items-center justify-between space-y-0">
              <CardTitle className="text-xs font-medium text-gray-500 uppercase tracking-wider">Issues</CardTitle>
              <AlertCircle className="w-4 h-4 text-orange-500" />
            </CardHeader>
            <CardContent className="p-5 pt-0">
              <div className="text-3xl font-semibold text-gray-900">3</div>
              <div className="flex items-center mt-1 text-xs text-orange-600 font-medium">
                <span>Needs attention</span>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Device List */}
          <div className="lg:col-span-2 space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold">Active Displays</h2>
              <Button variant="link" className="text-sm text-gray-500 h-auto p-0">View all</Button>
            </div>
            
            <div className="bg-white rounded-xl clean-border clean-shadow overflow-hidden">
              <div className="divide-y divide-gray-100/60">
                {[
                  { name: "Main Lobby", location: "Building A", status: "playing", playlist: "Welcome Loop", time: "2h remaining" },
                  { name: "Elevator Bank", location: "Building A", status: "playing", playlist: "Product Showcase", time: "Continuous" },
                  { name: "2nd Floor Conf", location: "Building B", status: "idle", playlist: "None scheduled", time: "Starts in 30m" },
                  { name: "Café Display", location: "Building C", status: "playing", playlist: "Lunch Menu", time: "Ends at 2:00 PM" },
                  { name: "Executive Suite", location: "Building A", status: "offline", playlist: "Corporate Comm", time: "Last seen 2h ago" },
                ].map((device, i) => (
                  <div key={i} className="p-4 flex items-center justify-between hover:bg-gray-50/50 transition-colors group">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-lg bg-gray-50 border border-gray-100 flex items-center justify-center">
                        <MonitorPlay className="w-5 h-5 text-gray-400" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h3 className="text-sm font-medium">{device.name}</h3>
                          {device.status === 'playing' && <span className="flex w-1.5 h-1.5 rounded-full bg-emerald-500"></span>}
                          {device.status === 'idle' && <span className="flex w-1.5 h-1.5 rounded-full bg-amber-400"></span>}
                          {device.status === 'offline' && <span className="flex w-1.5 h-1.5 rounded-full bg-red-500"></span>}
                        </div>
                        <p className="text-xs text-gray-500">{device.location}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-8">
                      <div className="hidden sm:block text-right">
                        <p className="text-sm font-medium text-gray-700">{device.playlist}</p>
                        <p className="text-xs text-gray-400">{device.time}</p>
                      </div>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Media Preview / Recent */}
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-base font-semibold">Recent Media</h2>
            </div>
            
            <div className="grid grid-cols-2 gap-3">
              {[
                { name: "Q3_Report.mp4", type: "Video", bg: "bg-blue-50 text-blue-600" },
                { name: "Welcome_Slide.jpg", type: "Image", bg: "bg-emerald-50 text-emerald-600" },
                { name: "Event_Promo_A.mov", type: "Video", bg: "bg-purple-50 text-purple-600" },
                { name: "Menu_Board_v2.png", type: "Image", bg: "bg-amber-50 text-amber-600" },
              ].map((media, i) => (
                <div key={i} className="group cursor-pointer">
                  <div className="aspect-[4/3] rounded-lg bg-gray-100 clean-border flex items-center justify-center mb-2 overflow-hidden relative">
                    <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors duration-200" />
                    <Film className="w-6 h-6 text-gray-300" />
                  </div>
                  <h4 className="text-xs font-medium truncate pr-2">{media.name}</h4>
                  <p className="text-[10px] text-gray-500 mt-0.5">{media.type}</p>
                </div>
              ))}
            </div>
            
            <Card className="mt-6 clean-border clean-shadow rounded-xl bg-white border-0">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="w-10 h-10 rounded-full bg-gray-50 flex items-center justify-center clean-border">
                  <CalendarDays className="w-4 h-4 text-gray-500" />
                </div>
                <div>
                  <h4 className="text-sm font-medium">Weekly Schedule</h4>
                  <p className="text-xs text-gray-500">3 playlists rotating today</p>
                </div>
                <Button variant="outline" size="sm" className="ml-auto h-7 text-xs">Edit</Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
