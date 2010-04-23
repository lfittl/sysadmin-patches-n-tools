#!/usr/bin/env ruby

f = IO.popen("conntrackd -i")

ips = {}
ips.default = 0

while line = f.gets do
        src_ip = line[/src=([0-9.]*)/, 1]
        ips[src_ip] += 1
end

ips.sort{|a,b| b[1]<=>a[1]}.to_a[0..50].each do |ip, conncount|
        puts "%15s - %d connections" % [ip, conncount]
end
