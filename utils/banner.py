from colorama import Back, Fore, Style, init

LIGHT_PURPLE    = '\033[38;2;100;100;255m'
PURPLE_BLUE     = '\033[38;2;100;100;255m'
LIGHT_PURPLE    = '\033[38;2;200;180;255m'
BOLD_WHITE      = '\033[1;37m'

def banner():
    print(f"""
          
{Fore.BLUE}{Style.BRIGHT}


                      +++++                      
                    ++{LIGHT_PURPLE}=   +{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}+                     
                    ++{LIGHT_PURPLE}+   ++{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}+                    
                    +++{LIGHT_PURPLE}+++{Style.RESET_ALL}{Fore.BLUE}{Style.BRIGHT}++*                    
                    *+++*+***                    
                     ********                    
                   {LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}**********                   
                  **{LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT} *********                  
                 ***{LIGHT_PURPLE}##{Fore.BLUE}{Style.BRIGHT}**********                 
               *****{LIGHT_PURPLE}###{Fore.BLUE}{Style.BRIGHT}***********{LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}              
           *********{LIGHT_PURPLE}####{Fore.BLUE} ******{LIGHT_PURPLE}########{Fore.BLUE}{Style.BRIGHT}          
 ++{LIGHT_PURPLE}+{Fore.BLUE}{Style.BRIGHT}++**************{LIGHT_PURPLE}###   #######{Fore.BLUE}{Style.BRIGHT}  *******++{LIGHT_PURPLE}++{Fore.BLUE}{Style.BRIGHT}++ 
+{LIGHT_PURPLE}++  +{Fore.BLUE}{Style.BRIGHT}**************{LIGHT_PURPLE}#       ##{Fore.BLUE}{Style.BRIGHT} *************  +{LIGHT_PURPLE}{Fore.BLUE}{Style.BRIGHT}++
++{LIGHT_PURPLE}+   +{Fore.BLUE}{Style.BRIGHT}***********  {LIGHT_PURPLE}#       #{Fore.BLUE}{Style.BRIGHT}*************+*  +{LIGHT_PURPLE}{Fore.BLUE}{Style.BRIGHT}++
 +++{LIGHT_PURPLE}++{Fore.BLUE}{Style.BRIGHT}******** {LIGHT_PURPLE}########   ###{Fore.BLUE}{Style.BRIGHT}*************++{LIGHT_PURPLE}++{Fore.BLUE}{Style.BRIGHT}++ 
        {LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}**{LIGHT_PURPLE}####{Fore.BLUE}{Style.BRIGHT}****** {LIGHT_PURPLE}###{Fore.BLUE}{Style.BRIGHT}***********          
              ************{LIGHT_PURPLE}###{Fore.BLUE}{Style.BRIGHT}*****               
                 **********{LIGHT_PURPLE}##{Fore.BLUE}{Style.BRIGHT}***                 
                  ********* {LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}**                  
                   ********* *                   
                    ******** {LIGHT_PURPLE}#{Fore.BLUE}{Style.BRIGHT}                   
                    *********                    
                    **+{LIGHT_PURPLE}**{Fore.BLUE}{Style.BRIGHT}+***                    
                    *+{LIGHT_PURPLE}+   +{Fore.BLUE}{Style.BRIGHT}++                    
                     +{LIGHT_PURPLE}+   +{Fore.BLUE}{Style.BRIGHT}++                    
                      ++{LIGHT_PURPLE}+{Fore.BLUE}{Style.BRIGHT}++                      

                    


   
{Style.RESET_ALL}
""")
