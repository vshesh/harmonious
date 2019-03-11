#terminascontroller2.rb
#terminal ruby program to get and transmit key info
#originally written for tcp by Robin Newman, April 2016
#this new version uses OSC messages updated December 2018
# use in conjunction with SP-KeyboardController2.rb running in Sonic Pi
require 'io/wait'
require 'socket'
require 'rubygems'
require 'osc-ruby'



@client = OSC::Client.new( 'localhost', 4559 )
def char_if_pressed #routine to scan for keyboard press (non-blocking)
begin
system("stty raw -echo") # turn raw input on
c = nil
if $stdin.ready?
c = $stdin.getc
end
c.chr if c
ensure
system "stty -raw echo" # turn raw input off
end
end

while true #main loop, runs until stopped by ctrl-c
k=0 #0 will remain 0 if no key pressed
c = char_if_pressed
k= "#{c}".ord if c #work out ascii value of key
# client = server.accept    # Wait for a client to connect
# client.puts k #transmit the keycode
# client.close #close the client terminating input
if k!=0 #only send message if k !=0
@client.send( OSC::Message.new( "/key" , k ))
end
sleep 0.005 #short gap
end