import pymysql



def convert_time(time:int):
    hours = time // 60

    minutes = time % 60


    if hours>0 and minutes >0:
        return f'{hours} {"hrs" if hours>1 else "hr"} {minutes} {"mins" if minutes>1 else "min"}'
    elif hours>0:
        return f'{hours} {"hrs" if hours>1 else "hr"}'
    else:
        return f'{minutes} {"mins" if minutes>1 else "min"}'

class Connection:
    def __init__(self,username: str, password:str , host: str = 'localhost'):
        self.username = username
        self.password  = password
        self.host = host
        self.error = False
        self.error_message = ''

    def reset_error(self):
        self.error = False
        self.error_message = ''
    
    def connect(self,dbname:str):
        self.database = dbname
        try:
            self.conn = pymysql.connect(
                host = self.host,
                user = self.username,
                password = self.password,
                database = self.database,
                cursorclass = pymysql.cursors.SSDictCursor,
                autocommit=True
            )
        
        except pymysql.Error as e:
            self.error = True
            self.error_message = str(e)
            return e
    
    def execute_query(self,query:str, args: tuple = ()) -> list:
        '''
            This method executes the given query with the given args
            Args:
                query: sql statement or prepared sql statement
                args: tuple of arguments for the prepared statement
            Returns:
                a list of all the rows returned from the query
        '''
        cur = self.conn.cursor()
        cur.execute(query,args)
        result = cur.fetchall()
        cur.close()
        return result


    def insert_into_table(self, table:str , fields:str , values:tuple ) -> None:

        query = f"INSERT INTO {table} {fields}"+ "\n" +  f"VALUES {values};"

        cur = self.conn.cursor()
        try:
            cur.execute(query)
        except pymysql.Error as e:
            self.error = True
            self.error_message = str(e)
            return e
        finally:
            cur.close()
        

    
    def call_procedure(self,proc: str ,args: tuple = ()) -> list:
        '''
            This method calls the given procedure with the given args
            Args:
                proc: name of the procedure
                args: tuple of arguments for the procedure
            Returns:
                a list of all the rows returned from the procedure
        '''
        cur = self.conn.cursor()
        result = []
        try:
            cur.callproc(proc,args)
            result = cur.fetchall()
        except pymysql.Error as e:
            self.error = True
            self.error_message = e.args[1]
            result = [] #return empty list if exception occured
        finally:
            cur.close()
            return result
    



    
class RecipeDb:
    def __init__(self,dbname : str ,connection: Connection):
        self.dbname = dbname
        self.conn = connection
        self.conn.connect(dbname)
    

    def get_top_recipes(self,limit:int = 8) -> list:
        #rows = self.conn.call_procedure('get_top_rated_recipes',(limit,))

        query = 'SELECT recipe_name FROM recipes ORDER BY rating DESC,recipe_name LIMIT %d;'%limit
        recipes = []
        rows = self.conn.execute_query(query)
        for row in rows:
            recipes.append(self.get_recipe(row['recipe_name']))
        
        return recipes

    def get_images_of_recipes(self,recipes:tuple = []) -> list:
        
        query = 'SELECT * FROM recipe_images IF recipe IN %s'%str(recipes);

        return self.conn.execute_query(query)
    
    def get_cuisine_names(self) -> list:
        return self.conn.call_procedure('get_all_cuisine_names')

    def get_all_recipe_categories(self) -> list:
        query = f'SELECT * FROM recipe_categories;'
        return self.conn.execute_query(query)
    
    def search_recipes(self,query:str,user_id:int = -1):
        query = f"%{query}%"
        if user_id == -1:
            rows = self.conn.call_procedure('search_recipe_without_user',(query,))
        
        else:
            rows = self.conn.call_procedure('search_recipe_with_user',(query,user_id))

        recipes = []
        for row in rows:
            recipes.append(self.get_recipe(row['recipe_name']))
        

        return recipes

    def get_recipes_by_category(self,category:str):
        rows = self.conn.call_procedure('get_recipes_by_category',(category,))
        recipes = []
        for row in rows:
            recipes.append(self.get_recipe(row['recipe_name']))
        
        return recipes

    def get_meal_plans(self):
        query = 'SELECT * FROM meal_plans;'
        return self.conn.execute_query(query)

    def toggle_like_meal_plan(self,user_id:int,meal_plan:str):
        self.conn.call_procedure('toggle_like_meal_plan',(user_id,meal_plan))
    
    def did_user_like_meal_plan(self,user_id:int,meal_plan:str):
        query=f'SELECT user_favorited_mealplan({user_id},"{meal_plan}") AS liked_count;'
        liked = self.conn.execute_query(query)
        liked = liked[0]['liked_count']
        return liked

    def get_recipes_by_cuisine(self,cuisine_name:str,user_id:int = -1):
        if user_id == -1:
            rows = self.conn.call_procedure('search_recipe_with_cuisine_without_user',(cuisine_name,))
        
        else:
            rows = self.conn.call_procedure('search_recipe_with_cuisine_with_user',(cuisine_name,user_id))
        

        recipes = []
        for row in rows:
            recipes.append(self.get_recipe(row['recipe_name']))
        
        return recipes
    
    def add_user(self,user : dict) -> None:
        try:
            values = (user['first_name'],user['last_name'],user['email'],user['password'],
                      user['avatar'])
            
            self.conn.call_procedure('create_user',values)
            
            user_id = self.get_user_by_email(user["email"],user["password"])

            self.add_user_preferences(user_id['user_id'],user['preferences'])
        
        except pymysql.Error as e:
            print(e)
            return e
        
        except Exception as e:
            print(e)
            return e
        
    
    def add_user_preferences(self,user_id: int , preferences:list) -> None:
        for preference in set(preferences):
            print(user_id,preference)
            try:
                self.conn.call_procedure('add_user_preference',(user_id,preference))
            except pymysql.Error as e:
                print(e)


    def delete_user(self,user_id:int):
        self.conn.call_procedure('delete_user_by_id',(user_id,))

    


    def get_user_by_email(self,email: str,password:str) -> dict:
        try:
            user = self.conn.call_procedure('get_user_by_email',(email,password))
            if len(user)> 0 :
                user = user[0]
                user['preferences'] = self.get_user_preferences(user['user_id'])
                return user
            else:
                return []
        except pymysql.Error as e:
            return e

    def get_user_preferences(self,user_id:int)->list:
        return self.conn.call_procedure('get_user_preferences',(user_id,))

    def get_recipe(self,recipe: str) -> dict:
        query = f'SELECT * FROM recipes WHERE recipe_name = "{recipe}";'
        result = self.conn.execute_query(query)
        if len(result) < 0:
            return []
        
        recipe_details = result[0]
    
        query = f'SELECT * FROM recipe_images WHERE recipe_name = "{recipe}";'
        recipe_details['images'] = self.conn.execute_query(query)
        
        recipe_details['rating'] = float(recipe_details['rating'])

        query = 'SELECT COUNT(DISTINCT(user_id))AS like_count FROM user_liked_recipes WHERE\n' + 'recipe_name = "%s";'%(recipe)
        
        
        like_count = self.conn.call_procedure('get_like_count_of_recipe',(recipe,))[0]['like_count']

        recipe_details['like_count'] = like_count
        return recipe_details
    
    def get_recipe_page_details(self,recipe:str)->dict:
        recipe_details = self.get_recipe(recipe)

        query = f'SELECT recipe_category_name FROM recipes_to_categories WHERE\n'+ 'recipe_name = "%s";'%(recipe)
        recipe_details['categories'] = self.conn.execute_query(query)

        query = f'SELECT ingredient_name,quantity FROM recipe_ingredients WHERE\n'+ 'recipe_name = "%s";'%(recipe)
        recipe_details['ingredients'] = self.conn.execute_query(query)

        query = 'SELECT step_number,instruction FROM recipe_instructions WHERE\n' +'recipe_name = "%s";'%(recipe)
        recipe_details['steps'] = self.conn.execute_query(query)

        

        p = recipe_details['preparation_time']
        c = recipe_details['cooking_time']
        recipe_details['prep_time'] = convert_time(p)
        recipe_details['cook_time'] = convert_time(c)
        recipe_details['total_time'] = convert_time(p+c)


        return recipe_details
    
    def toggle_like_recipe(self,user_id:int,recipe_name:str):
        self.conn.call_procedure('toggle_like_recipe',(user_id,recipe_name))

    def get_ingredient_details(self,ing:str):

        query = f'SELECT * FROM ingredients WHERE ingredient_name = "%s";' %ing
        try:
            return self.conn.execute_query(query)[0]
        except Exception as e:
            print(e) 
    
    def get_ingredient(self,ing:str):
        ingr = self.conn.call_procedure('get_ingredient',(ing,))[0]
        ingr['store_links'] = self.conn.call_procedure('get_store_links',(ing,))
        return ingr

    def get_user_review_of_recipe(self,user_id:int,recipe:str):
        try:
            query = f'SELECT * FROM user_comments WHERE user_id = {user_id} AND recipe_name = "{recipe}";'
            return self.conn.execute_query(query)
            
        except Exception as e:
            print(e)
            return e

    def did_user_liked_recipe(self,user_id:int,recipe:str):
        query = f'SELECT user_liked_recipe({user_id},"{recipe}") AS liked;'
        result = self.conn.execute_query(query)
        print(result)
        return result[0]['liked']

    def edit_preferences(self,user_id:int,preferences:list):
        self.conn.call_procedure('delete_user_preferences',(user_id,))
        print(preferences)
        for preference in set(preferences):
            self.conn.call_procedure('add_user_preference',(user_id,preference))

    def get_user_names(self,user_id:int):
        try:
            query = f'SELECT first_name,last_name FROM users WHERE user_id = {user_id};'
            row = self.conn.execute_query(query)[0]
            return row['first_name'],row['last_name']
            
        except Exception as e:
            print(e)
            return "",""

    def get_all_reviews_of_recipe(self,recipe:str):
        try:
            query = f'SELECT * FROM user_comments WHERE recipe_name = "{recipe}";'
            rows = self.conn.execute_query(query)
            for row in rows:
                row['date'] = self.format_date(row['commented_datetime'])
                row['first_name'],row['last_name'] = self.get_user_names(row['user_id'])
                row['avatar'] = self.get_avatar_link(row['user_id'])
            
            return rows
            
        except Exception as e:
            print(e)
            return []
    

    def get_all_avatars(self) -> list:
        try:
            query = f'SELECT * FROM avatars;'
            rows = self.conn.execute_query(query)
            return rows
            
        except Exception as e:
            print(e)
            return []
        
    
    def get_most_liked_cuisines(self):
        cuisines = []
        liked_counts = []
        for cuisine in self.get_cuisine_names():
            cuisine = cuisine['cuisine_name']
            cuisines.append(cuisine)
            liked_count = self.conn.call_procedure('get_liked_recipe_count_by_cuisine',(cuisine,))
            print(cuisine,liked_count)
            liked_counts.append(liked_count[0]['liked_recipe_count'])
        
        return cuisines,liked_counts

    def get_top_rated_recipes(self,limit=300):
        recipes = []
        ratings = []
        rows = self.conn.call_procedure('get_top_rated_recipes',(1300,))
        for row in rows:
            recipes.append(row['recipe_name'])
            ratings.append(row['rating'])
        
        return recipes,ratings
    
    def get_user_count_by_preference(self):
        preferences = ['vegan','vegetarian','egg','gluten-free','meat']
        user_counts = []
        

        for preference in preferences:
            count = self.conn.call_procedure('get_user_count_by_preference',(preference,))
            if len(count) > 0:
                count = count[0]['user_count']
            else:
                count = 0
            
            user_counts.append(count)
        
        return preferences,user_counts

        
    def post_user_review(self,user_id:int,recipe:str,comment:str,rating:float):
        try:
            args = (user_id,recipe,rating,comment)
            self.conn.call_procedure('rate_recipe',args)
        
        except Exception as e:
            print(e)
            return e
    

    def delete_review(self,user_id:int,recipe:str):
        try:
            args = (user_id,recipe)
            self.conn.call_procedure('delete_comment',args)
        
        except Exception as e:
            print(e)
            return e
    

    def format_date(self,date):
        year = self.conn.execute_query(f'SELECT YEAR(CONVERT("{date}",DATETIME)) AS year;')[0]['year']
        day = self.conn.execute_query(f'SELECT DAY(CONVERT("{date}",DATETIME)) AS day;')[0]['day']
        month = self.conn.execute_query(f'SELECT MONTH(CONVERT("{date}",DATETIME)) AS month;')[0]['month']

        monthName = self.conn.execute_query(f'SELECT MONTHNAME(CONVERT("{date}",DATETIME)) AS month;')[0]['month']
          

        yearCurrent = self.conn.execute_query(f'SELECT YEAR(NOW()) AS year;')[0]['year']
        dayCurrent = self.conn.execute_query(f'SELECT DAY(NOW()) AS day;')[0]['day']
        monthCurrent = self.conn.execute_query(f'SELECT MONTH(NOW()) AS month;')[0]['month']

        if (yearCurrent - year) > 5:
            return f"{(yearCurrent - year)} years ago"
        
        elif (yearCurrent - year) > 1:
            return f"{month}/{day}/{year}"
        
        elif (yearCurrent - year) == 1:
            return f"{monthName} {day}"
        
        else: #Same Year
            if monthCurrent > month:
                return f"{monthName} {day}"
            
            else: #Same month
                if dayCurrent - day > 7:
                    return f"{(dayCurrent - day)} days ago"
                
                elif dayCurrent - day > 1:
                    dayName = self.conn.execute_query(f'SELECT DAYNAME(CONVERT("{date}",DATETIME)) AS day;')[0]['day']
                    return f"{dayName}"
                
                elif dayCurrent - day == 1:
                    return "Yesterday"
                
                else: # Same day
                    hours = self.conn.execute_query(f'SELECT HOUR(CONVERT("{date}",DATETIME)) AS hours;')[0]['hours']
                    mins = self.conn.execute_query(f'SELECT MINUTE(CONVERT("{date}",DATETIME)) AS mins;')[0]['mins']
                    secs = self.conn.execute_query(f'SELECT SECOND(CONVERT("{date}",DATETIME)) AS secs;')[0]['secs']

                    hoursCurrent = self.conn.execute_query(f'SELECT HOUR(NOW()) AS hours;')[0]['hours']
                    minsCurrent = self.conn.execute_query(f'SELECT MINUTE(NOW()) AS mins;')[0]['mins']
                    secsCurrent = self.conn.execute_query(f'SELECT SECOND(NOW()) AS secs;')[0]['secs']

                    if hoursCurrent > hours:
                        return f"{hoursCurrent - hours} hour{'s' if hoursCurrent - hours >1 else ''} ago"
                    
                    elif minsCurrent > mins:
                        return f"{minsCurrent - mins} min{'s' if minsCurrent - mins >1 else ''} ago"
                    
                    else:
                        return f"{secsCurrent - secs} second{'s' if secsCurrent - secs >1 else ''} ago"




    def get_avatar_link(self,user_id : int):
        query = f'SELECT avatar_link FROM avatars JOIN users ON users.avatar = avatars.avatar_id\n'+f'WHERE user_id = {user_id}'
        return self.conn.execute_query(query)[0]['avatar_link']

        
    
    def close_connection(self):
        self.conn.conn.close()
    