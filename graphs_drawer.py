import matplotlib
matplotlib.use('Agg')  # Use a non-interactive backend

import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os

def save_user_counts_plot_as_image(preferences, user_counts,  filename='user_counts_per_preference.png',dpi=300):
    preferences = [pref for pref, count in zip(preferences, user_counts) if count > 0]
    user_counts = [count for count in user_counts if count > 0]
    # Set the overall aesthetics
    sns.set_theme(style="whitegrid")
    sns.set_palette("tab10")
    # Create a figure for the pie chart
    plt.figure(figsize=(2, 2))  # Adjust the size as needed

    # Create a pie chart
    plt.pie(user_counts, labels=preferences, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.

    # Set the title of the pie chart
    #plt.title('User Preferences Distribution', fontsize=16)

    # Save the plot as an image file with higher DPI
    plt.savefig(os.path.join('static', filename), bbox_inches='tight', dpi=dpi)
    plt.close() # Close the figure to free memory



def plot_top_rated_recipes(recipe_names, ratings,dpi=300):


    # Set the overall aesthetics
    sns.set_theme(style="whitegrid")
    sns.set_palette("flare")

    data = pd.DataFrame({'Recipe': recipe_names, 'Rating': ratings})

    # Find representative recipes for each whole number rating
    representative_recipes = {}
    for rating in range(0, 6):  # Whole number ratings from 0 to 5
        recipes_with_rating = data[data['Rating'] == rating]
        if not recipes_with_rating.empty:
            # Select the recipe with the shortest name
            representative_recipes[rating] = recipes_with_rating.loc[recipes_with_rating['Recipe'].str.len().idxmin(), 'Recipe']

    # Create a line plot
    plt.figure(figsize=(3,3))
    plt.plot(data['Recipe'], data['Rating'], linestyle='-', color='b')  # No marker

    # Set x-axis labels to show representative recipe names for non-overlapping ratings
    selected_ratings = [0.0, 2.5, 5.0]  # Adjust as needed based on your data
    plt.xticks(ticks=[data[data['Recipe'] == representative_recipes.get(rating, '')].index[0] for rating in selected_ratings if rating in representative_recipes],
               labels=[representative_recipes.get(rating, '') for rating in selected_ratings if rating in representative_recipes],
               rotation=45, ha='right', fontsize=4)

    # Set the title and labels
    #plt.title('Recipe Ratings with Selective Recipe Labels', fontsize=14)
    plt.ylabel('Rating', fontsize=12)
    plt.xlabel('Recipes', fontsize=12)

    # Improve layout
    plt.tight_layout()

    # Save the plot as an image file
    plt.savefig(os.path.join('static', 'top_rated_recipes.png'), bbox_inches='tight', dpi=dpi)
    plt.close()


def plot_most_liked_cuisines(cuisines, liked_counts,dpi=300):
    cuisines = [cus for cus, count in zip(cuisines, liked_counts) if count > 0]
    liked_counts = [count for count in liked_counts if count > 0]

    # Set the overall aesthetics
    sns.set_theme(style="whitegrid")

    plt.figure(figsize=(2, 2))
    plt.pie(liked_counts, labels=cuisines, autopct='%1.1f%%', startangle=140)

    # Draw a circle at the center of pie to make it look like a donut
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)

    # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.axis('equal')  



    # Save the plot as an image file
    plt.savefig(os.path.join('static', 'most_liked_cuisines.png'), bbox_inches='tight', dpi=dpi)
    plt.close()