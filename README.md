# Roblox has patched this method as of late 2024 due to the game API only returning a max of 5 thumbnails in a server.
## There is no other method I am aware of currently to make this work.
<br>

# RobloxStreamSniper
Simple Roblox stream sniper, wrote this because I was bored and didn't find any other working ones.  
  
~~Currently slow due to being single-threaded, but feel free to fork it and add parallelization.~~  
Added multithreading, should be significantly faster, you can also now select whether to sort by biggest, smallest, or interwoven.  
  
Credits to RoSniperX by Lukas Dobbles, I analyzed most of their code to figure out how to write it in python.  

## Requirements -
- colorama
- requests
