# BlockMail - A blockchain-based Email System

## Running the Frontend of BlockMail

In order to test the frontend of BlockMail, you will need to use software which simulates a web server on your PC, so that the cookies required for it to work can be stored correctly. I recommend using a Tool named XAMPP to do so:

1.	Download XAMPP for Windows from https://www.apachefriends.org/index.html
2.	Install XAMPP using the default installation options.
3.	Open XAMPP and start the Apache server (if not already running).
4.	Go to C:\xampp\htdocs and create a folder named “BlockMail”.
5.	Copy the contents of the “Frontend” folder to the BlockMail folder which you have just made.
6.	Open your web browser, and go to http://localhost/blockmail/

You should now be able to use the BlockMail frontend as intended!

If you run into any problems at all when following these instructions, please contact me at t.d.herring@se17.qmul.ac.uk and I will get back to you as soon as possible to assist.

## Testing the BlockMail Network (Backend) Locally

*Note:* The suggested setup when testing locally is 2 Master Nodes and 2 Normal Nodes. Anything more than this may slow down your system substantially. With this in mind, please follow the instructions below:

In the [Node Client](https://github.com/tdherring/BlockMail/tree/master/Node%20Client) folder you will find a couple of other folders named [Master Nodes](https://github.com/tdherring/BlockMail/tree/master/Node%20Client/Master%20Nodes) and [Nodes](https://github.com/tdherring/BlockMail/tree/master/Node%20Client/Nodes). 

Each contains a number of pre-configured nodes that can be launched to simulate a working BlockMail environment. There are several requirements:

* You must run the Master Nodes first.
* You must run at least 2 Master Nodes.
* You must run the nodes on a Windows PC.
* If you wish to test across multiple PCs, you'll need to ensure that the "server_ip" attribute in config.json is set to your external IP address, and that ports 41285-41288 are open on your local PC firewall and/or network firewall. 
  * If you change the IP of the master nodes, you will have to reflect this by modifying the "master_nodes" attribute in config.json in all other nodes.
  * You will also have to change the MASTER_NODES constant in [Frontend](https://github.com/tdherring/BlockMail/tree/development/Frontend)/[js](https://github.com/tdherring/BlockMail/tree/development/Frontend/js)/[constants.js](https://github.com/tdherring/BlockMail/blob/development/Frontend/js/constants.js)
  
You can view the status of the network on the "Network Overview" page of the frontend.

## Troubleshooting

### I see "[TIME] This machine's time is too inaccurate. Please resynchronise with an NTP server and restart the client."

1. Go to the Windows Start menu, and click on the settings cog.
2. Search for "Date and Time Settings".
3. Click on "Sync now", and relaunch the node client.

### On the website, I see "Unable to Connect to the BlockMail network. Try again?"

* Ensure that the nodes are running. 
* If the nodes are already running, and you have changed the IP address of the master nodes, ensure that this is reflected in [Frontend](https://github.com/tdherring/BlockMail/tree/development/Frontend)/[js](https://github.com/tdherring/BlockMail/tree/development/Frontend/js)/[constants.js](https://github.com/tdherring/BlockMail/blob/development/Frontend/js/constants.js).

### My Node client hangs sometimes

* If running multiple nodes on the same computer, the processor may become locked up in dealing with other nodes as a result of the highly threaded nature of the BlockMail client. To resolve the issue simply press any key to "wake" the thread.
* When running one node (as in an actual deployment) this issue has not shown yet and should not cause problems.

### Other issues

* If a critical error occurs, the easiest solution would be to reset the blockchain on each of the nodes. This can be done by removing the "blocks" and "temp" folders in each instances directory.
