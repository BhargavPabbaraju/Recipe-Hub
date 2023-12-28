from flask import Flask, render_template, request, redirect,session,url_for,flash

from settings import *
from db_connections import Connection,RecipeDb

from graphs_drawer import save_user_counts_plot_as_image,plot_top_rated_recipes,plot_most_liked_cuisines

app = Flask(__name__)
app.secret_key = "super secret key"

conn = Connection(username=USERNAME,password=PASSWORD,host=HOST)
recipe_db = RecipeDb(dbname=DBNAME,connection=conn)






@app.route("/")
def home_page(recipes = None):
    if 'user' not in session:
        session['user'] = None
   
    if 'cuisines' not in session:
        session['cuisines'] = recipe_db.get_cuisine_names()
        
        
    session['page'] = 'Home'
    if not recipes:
         recipes = recipe_db.get_top_recipes()
    if conn.error:
            flash(conn.error_message)
    
    if session['user']:
        user_id = session['user']['user_id']
        for recipe in recipes:
            recipe['user_liked_recipe'] = recipe_db.did_user_liked_recipe(
                user_id,recipe['recipe_name'])
     
    return render_template(
        "home.html",
        recipes = recipes,
        categories = recipe_db.get_all_recipe_categories()
    )


@app.route('/like_recipe',methods=['GET'])
def like_recipe():
    recipe_name = session['recipe']['recipe_name']
    user_id = session['user']['user_id']
    recipe_db.toggle_like_recipe(user_id,recipe_name)

    return redirect(url_for("recipe",recipe_name=session['recipe']['recipe_name']))

@app.route('/recipe/<recipe_name>')
def recipe(recipe_name):
    recipe = recipe_db.get_recipe_page_details(recipe_name)
    session['recipe'] = recipe
    ingredients = {}
    for ingredient in recipe['ingredients']:
        ing = ingredient['ingredient_name']
        ingredients[ing] = recipe_db.get_ingredient_details(ing)
    
    reviews = recipe_db.get_all_reviews_of_recipe(recipe_name)

    if session['user']:
        user_id = user_id = session['user']['user_id']
        user_review = recipe_db.get_user_review_of_recipe(user_id,recipe_name)
        
        user_liked_recipe = recipe_db.did_user_liked_recipe(user_id,recipe_name)

    else:
        user_review = None
        user_liked_recipe = False

    session['page'] = 'Recipe'
    return render_template('recipe.html', recipe=recipe,
                           ingredients = ingredients,
                           reviews=reviews,
                           user_review = user_review,
                           user_liked_recipe = user_liked_recipe)


@app.route("/login", methods=['POST','GET'])
def login():

    session['page'] = 'Login'

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            user = recipe_db.get_user_by_email(email,password)
            if conn.error:
                flash(conn.error_message,'error')
                return render_template(
                    "login_page.html",
                )
            session['user'] = user
            return redirect('/')
             
        except Exception as e:
             if conn.error:
                flash(conn.error_message,'error')
                return render_template(
                    "login_page.html",
                )
        if conn.error:
            flash(conn.error_message,'error')
            return render_template(
                "login_page.html",
            )

        
            
            
    

    
    else:
        return render_template(
            "login_page.html",
        )
    

@app.route("/trends")
def trends():
    save_user_counts_plot_as_image(*recipe_db.get_user_count_by_preference())
    plot_top_rated_recipes(*recipe_db.get_top_rated_recipes())
    plot_most_liked_cuisines(*recipe_db.get_most_liked_cuisines())
    return render_template("trends.html")


@app.route("/post_comment", methods=['POST'])
def post_comment():
    if request.method == 'POST':
        recipe_db.post_user_review(user_id = int(session['user']['user_id']),
                                   recipe = session['recipe']['recipe_name'],
                                   comment = request.form['comment'],
                                   rating = float(request.form['rating']))

        if conn.error:
                print(conn.error_message)
                return f"<h1>{conn.error_message}</h1>"
        
    return redirect(url_for("recipe",recipe_name=session['recipe']['recipe_name']))

@app.route('/delete_review', methods=['POST'])
def delete_review():
    recipe_db.delete_review(user_id = int(session['user']['user_id']),
                            recipe = session['recipe']['recipe_name'])
    return redirect(url_for("recipe",recipe_name=session['recipe']['recipe_name']))



@app.route("/search",methods=['POST'])
def search():
    query = request.form['query']
    user_id = session['user']['user_id'] if session['user'] else -1
    recipes = recipe_db.search_recipes(query,user_id)
    if len(recipes)<1:
        flash("Your search doesn't match your preferences","error")

    return render_template("search_result.html",recipes=recipes)
    
@app.route("/cuisine/<cuisine_name>")
def cuisine(cuisine_name):
    user_id = session['user']['user_id'] if session['user'] else -1
    recipes = recipe_db.get_recipes_by_cuisine(cuisine_name,user_id)
    if len(recipes)<1:
              flash("No recipes with that cuisine","error")
    return render_template("search_result.html",recipes=recipes)
          
@app.route("/category/<category_name>")
def category(category_name):
    recipes = recipe_db.get_recipes_by_category(category_name)
    if len(recipes)<1:
              flash("No recipes with that category","error")
    return render_template("search_result.html",recipes=recipes)

@app.route("/profile")
def profile():
     session['page'] = 'Profile'
     return render_template(
            "profile.html",
            avatar = recipe_db.get_avatar_link(session['user']['user_id'])
        )

@app.route("/register", methods=['POST','GET'])
def register():
    session['page'] = 'Register'
    if request.method == 'POST':
        user = {}
        user['first_name'] = request.form['firstName']
        user['last_name'] = request.form['lastName']
        user['email'] = request.form['email']
        user['password'] = request.form['password']
        user['preferences'] = request.form.getlist('preferences')  # Assuming preferences are checkboxes
        user['allergies'] = request.form.getlist('allergies') 
        user['avatar'] = request.form['avatar']
       
        recipe_db.add_user(user)
        if conn.error:
            flash(conn.error_message,'error')
            return redirect(url_for("register"))
        
        session['user'] = recipe_db.get_user_by_email(user['email'],user['password'])
        print(session['user'])
        
        
        session['user']['preferences'] = recipe_db.get_user_preferences(session['user']['user_id'])
        
        return redirect('/')
        
        
        
        
        

    
    else: #Get request
        return render_template(
        "register.html",
        avatars = enumerate(recipe_db.get_all_avatars())
    )

@app.route("/logout", methods=['POST'])
def logout():
    session['user'] = None
    return redirect(url_for("home_page"))

@app.route("/meal_plans")
def meal_plans():
     meal_plans = recipe_db.get_meal_plans()
     if session['user']:
          user_id = session['user']['user_id']
          for i in range(len(meal_plans)):
               meal_plans[i]['liked_by_user'] = recipe_db.did_user_like_meal_plan(
                    user_id,meal_plans[i]['meal_plan_name']
               )
     return render_template("meal_plans.html",
                            meal_plans = meal_plans)

@app.route("/like_meal_plan/<meal_plan>",methods=['POST','GET'])
def like_meal_plan(meal_plan):
    if session['user']:
        user_id = session['user']['user_id']
        recipe_db.toggle_like_meal_plan(user_id,meal_plan)
    return redirect(url_for("meal_plans"))


@app.route("/edit_preferences",methods=['POST'])
def edit_preferences():
    if session['user']:
        user_id = session['user']['user_id']
        recipe_db.edit_preferences(user_id,request.form.getlist('preferences'))
        session['user'] = recipe_db.get_user_by_email(
            session['user']['email'],
            session['user']['password'],
        )
    return redirect(url_for("profile"))

@app.route("/delete_account",methods=['POST'])
def delete_account():
    user_id = session['user']['user_id']
    recipe_db.delete_user(user_id)
    session['user'] = None
    return redirect(url_for("home_page"))

@app.route("/ingredient/<ingredient_name>")
def ingredient(ingredient_name):
    ing = recipe_db.get_ingredient(ingredient_name)
    return render_template("ingredient.html",ing = ing)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)