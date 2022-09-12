import random
import time
from typing import Dict,List,Any,Union
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from utils.utils import solve_captch
from rich.console import Console

class Reporter(webdriver.Remote):

    def __init__(self,profile_name:str,profile_uuid:str, urls:List[str], command_executor:str, destroy_browser:bool = True , tracker:List = [] ) -> None:
        self.command_executor = command_executor
        # self.capabilities = desired_capabilities
        self.profile_name = profile_name
        self.profile_uuid = profile_uuid
        self.urls = urls
        self.destroy_browser = destroy_browser
        self.console = Console()
        self.tracker = tracker

        super(Reporter,self).__init__(self.command_executor,desired_capabilities={})
        self.set_page_load_timeout(120)
        self.implicitly_wait(120)


    def start_reporting(self):
        """
        Starts reporting for the urls and profile given in the initial
        """
        for url in self.urls:
            
            self.tracker.append({
                'profile':self.profile_name,
                'exists':True,
                'url':url
            })


            if self.get_page(url):
                captcha = self.solve_captcha()
                logged_in = self.is_profile_logged_in()

                self.tracker[-1]['captcha_solved'] = captcha
                self.tracker[-1]['Logged_in'] = logged_in

                if captcha and logged_in:
                    self.move_mouse_around()
                    self.click_helpful_button()
                elif not logged_in:
                    break
                else:
                    continue

        self.quit()

    def get_page(self,url:str) -> None:
        """
        gets the url in the browser.\n
        parameters:\n
        url:<str>
        returns:\n
        None
        """
        attempts = 0
        url_open = False
        while not url_open:
            self.get(url)
            if self.find_elements(By.ID,"nav-logo") or "Try different image" in self.page_source:
                url_open = True
                print("page loaded")
            if attempts >= 3:
                print("page not loaded")
                break
            attempts +=1
        return url_open
    def solve_captcha(self) -> bool:
        """
        Checks if captcha appreared on the page.if appeared will try to solve it.
        return:
        True  : if captcha was solved
        False : if captcha was not solved
        """

        if "Try different image" in self.page_source:
            print(f"Captcha appear for profile [{self.profile_uuid}]")
            if not solve_captch(self):
                print(self.profile_name, "CAPTCHA not solved")
                return False
        return True
    
    def is_profile_logged_in(self) -> bool:
        """
        Checks if the multilogin is logged into amazon \n
        returns:\n
        True  : if the profile is logged in
        False : if the profile is not logged in
        """

        if self.find_elements(By.CSS_SELECTOR, 'a[data-csa-c-content-id="nav_youraccount_btn"]'):
            self.tracker[-1]['Logged_in'] = True
            return True
        self.console.log(f"{self.profile_name}:Profile not logged in into Amazon account",style='red')
        return False

    def click_helpful_button(self) -> bool:
        """
        Clicks abuse button for the review.
        """

        helpful_btns = self.find_elements(By.CSS_SELECTOR, "input[data-hook='vote-helpful-button']")
        if helpful_btns:
            actions = ActionChains(self)
            self.execute_script("arguments[0].scrollIntoView(true);", helpful_btns[0])
            actions.move_to_element(helpful_btns[0]).pause(1).click().perform()
            time.sleep(10)
            msg = self.find_elements(By.CSS_SELECTOR,'span[data-hook="vote-success-message"] div.a-alert-content')
            print(msg[0].get_attribute('text'))
            if msg[0].text == "Thank you for your feedback.":
                self.console.log(f"[{self.profile_name}] [Helpful button] clicked" , style="blue")
                return True
        else:
            self.console.log(f"[{self.profile_name}] [Helpful button] not found" , style="red")
            return False


    def move_mouse_around(self):
        """
        moves mouse arounds the screen in random pattern.
        """
        elements = self.find_elements(By.CSS_SELECTOR,'a')
        # elements = list(filter(lambda x : x.is_displayed() , elements))
        actions = ActionChains(self)
        length_of_elements = len(elements)
        if elements:
            for _ in range(length_of_elements if length_of_elements <= 5 else 5):
                try:
                    move_to = random.choice(elements)
                    self.execute_script("arguments[0].scrollIntoView(true);", move_to)
                    time.sleep(2)
                    actions.move_to_element(random.choice(elements)).pause(2).perform()
                    time.sleep(4)
                    actions.reset_actions()
                except:
                    pass
        time.sleep(2)

       

    def bring_inside_viewport(self,selector:str='[id^=CardInstance]'):
        """
        brings a element to the center of viewport
        """
        recommendations = self.find_element(By.CSS_SELECTOR,selector)
        if recommendations:
            desired_y = (recommendations.size['height'] / 2) + recommendations.location['y']
            window_h = self.execute_script('return window.innerHeight')
            window_y = self.execute_script('return window.pageYOffset')
            current_y = (window_h / 2) + window_y
            scroll_y_by = desired_y - current_y
            self.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)




    def __exit__(self, *args) -> None:
        if self.destroy_browser:
            self.quit()


