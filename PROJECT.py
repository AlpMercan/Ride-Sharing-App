#!/usr/bin/env python
# coding: utf-8

# In[ ]:





# In[1]:


import sqlite3
ADMIN_ID = '1907'
ADMIN_PASSWORD = '10'
# to get some user ids & passwords
con = sqlite3.connect('database1.db')
cur = con.cursor()

print('Passengers:')
for row in cur.execute('SELECT Passenger_ID, Password FROM Passenger WHERE Passenger_ID IN (SELECT Passenger_ID FROM Passenger)'):
    print(row)

print('\nDrivers:')
for row in cur.execute('SELECT Driver_ID, Password FROM Driver WHERE Driver_ID IN (SELECT Driver_ID FROM Driver)'):
    print(row)


con.close()





# import
import random
import sqlite3
import PySimpleGUI as sg
from datetime import datetime
import math
from datetime import datetime
window_stack = []
# connect to the DB

con = sqlite3.connect('database1.db')
cur = con.cursor()
# global variables
selected_driver_id= None
login_user_id = -1
login_user_name = -1
login_user_type = -1
counter=0
approved_counter=0
# window functions
def window_login():
    
    layout = [[sg.Text('Welcome to the Course Management System. Please enter your information.')],
              [sg.Text('ID:',size=(10,1)), sg.Input(size=(10,1), key='id')],
              [sg.Text('Password:',size=(10,1)), sg.Input(size=(10,1), key='password')],
              [sg.Button('Login')]]

    return sg.Window('Login Window', layout)

def window_passenger():
    layout = [
        [sg.Text('Welcome ' + login_user_name)],
        [sg.Button('Transactions')],
        [sg.Button('Vehicle Call')],
        [sg.Button('Your Trips')],  
        [sg.Button('Logout')]
    ]

    return sg.Window('passenger', layout)


    
def window_driver():
    layout = [
        [sg.Text('Welcome ' + login_user_name)],
        [sg.Button('Transactions')],
        [sg.Button('View Trips')],
        [sg.Button('Toggle Status')],
        [sg.Button('Deliver Passenger')],
        [sg.Button('Logout')]
    ]
    return sg.Window('driver', layout)

 
def button_login(values):
    global login_user_id
    global login_user_name
    global login_user_type
    global window
    global ADMIN_ID
    global ADMIN_PASSWORD
    
    uid = values['id']
    upass = values['password']

    if uid == '':
        sg.popup('ID cannot be empty')
    elif upass == '':
        sg.popup('Password cannot be empty')
    else:
        if uid == ADMIN_ID and upass == ADMIN_PASSWORD:
            # This is an admin
            login_user_type = 'Admin'
            sg.popup('Welcome, Admin!')
            window.close()
            window = window_admin() # this is the admin window, which you will create next
        else:
            
            cur.execute('SELECT User_ID, Name FROM User WHERE User_ID = ? AND Password = ?', (uid,upass))
            row = cur.fetchone()
            # this is some existing user, let's keep the ID of this user in the global variable
            login_user_id = row[0]
            
            # we will use the name in the welcome message
            login_user_name = row[1]
            
            # now let's find which type of user this login_user_id belongs to
            # let's first check if this is a student
            cur.execute('SELECT Driver_ID FROM Driver WHERE Driver_ID = ?', (uid,))
            row_driver = cur.fetchone()
            
            if row_driver is None:
                # this is not a driver, let's check for passenger
                cur.execute('SELECT Passenger_ID FROM Passenger WHERE Passenger_ID = ?', (uid,))
                row_passenger = cur.fetchone()
                if row_passenger is None:
                    # this is not a teacher also, then there should be some problem with the DB
                    # since we expect a user to be either a student or a teacher
                    sg.popup('User type error! Please contact the admin.')
                else:
                    # this is a passenger
                    login_user_type = 'passenger'
                    sg.popup('Welcome, ' + login_user_name + ' (passenger)')
                    window.close()
                    window = window_passenger()
            else:
                # this is a driver
                    login_user_type = 'Driver'
                    sg.popup('Welcome, ' + login_user_name + ' (Driver)')
                    window.close()
                    window = window_driver()
def window_vehicle_call(drivers):
    # Filter the drivers based on their status
    available_drivers = [driver for driver in drivers if driver[3] == 'Available']  # 'Status' is at index 3
    driver_list = [[f'{driver[0]} - {driver[1]} ({driver[2]})'] for driver in available_drivers]  # Display available driver info

    layout = [
        [sg.Text('Filter by Car:'), sg.Input(size=(10,1), key='car_filter')],
        [sg.Button('Filter')],
        [sg.Text('Available Drivers:')],
        [sg.Listbox(driver_list, size=(30, 6), key='driver_list')],
        [sg.Button('Proceed to Payment')]
    ]

    return sg.Window('Vehicle Call', layout)



def button_deliver_passenger():
    # Check the Trip_Creation table to find a matching Driver_ID to the user's ID
    cur.execute('SELECT * FROM Trip_Creation WHERE Driver_ID = ?', (login_user_id,))
    trip_creations = cur.fetchall()

    if trip_creations:
        for trip_creation in trip_creations:
            passenger_id = trip_creation[0]
            trip_id = trip_creation[1]

            # Go to the Trip table and check Trip_Status
            cur.execute('SELECT Trip_Status, Trip_Distance, Fee, Trip_Start_Date FROM Trip WHERE Trip_ID = ?', (trip_id,))
            trip_info = cur.fetchone()

            if trip_info is not None and trip_info[0] == 'Passenger is in the car':
                # Change the trip status to 'Delivered'
                cur.execute('UPDATE Trip SET Trip_Status = ? WHERE Trip_ID = ?', ('Delivered', trip_id))

                # Store the Trip_Distance in a variable
                trip_distance = trip_info[1]
                trip_fee = trip_info[2]
                print(trip_fee)
                date= trip_info[3]
                
                # By using the stored Passenger_ID, go to the Credit_Card
                cur.execute('SELECT * FROM Credit_Card WHERE Passenger_ID = ?', (passenger_id,))
                passenger_cards = cur.fetchall()

                if passenger_cards:
                    # Assuming the first card is to be used for payment
                    payment_card_id = passenger_cards[0][0]

                    # Generate a unique payment_id
                    while True:
                        payment_id = random.randint(1, 999999)  # Assuming the payment_id is a six-digit number
                        cur.execute('SELECT * FROM Payment WHERE Payment_ID = ?', (payment_id,))
                        if cur.fetchone() is None:
                            break

                    # Insert into Payment table
                    cur.execute('INSERT INTO Payment (Payment_ID, Method, Card_No, Payment_Date, Payment_Type, Amount) VALUES (?, ?, ?, ?, ?, ?)', 
                                (payment_id, 1, payment_card_id, date, "Credit", trip_fee))

                    # Create a new transaction entry
                    cur.execute('INSERT INTO Transactions (Trip_ID, Payment_ID) VALUES (?, ?)', 
                                (trip_id, payment_id))

                    con.commit()

                    window = window_payment(passenger_cards)
                    window.read()
                    window.close()

                else:
                    sg.popup('No credit cards found for the passenger.')
                
                sg.popup('Passenger Delivered.')

    else:
        sg.popup('No trips found for the driver.')


        
def window_admin():
    layout = [[sg.Text("Admin Panel")],
              [sg.Button('Create Address')],
              [sg.Button('Review Edit')],
              [sg.Button('Logout')]]
    return sg.Window('Admin Window', layout)

def window_create_address():
    layout = [
              [sg.Text('Street'), sg.Input(key='Street')],
              [sg.Text('City'), sg.Input(key='City')],
              [sg.Text('Zip Code'), sg.Input(key='Zip_Code')],
              [sg.Text('X_Cord'), sg.Input(key='X_Cord')],
              [sg.Text('Y_Cord'), sg.Input(key='Y_Cord')],
              [sg.Button('Submit'), sg.Button('Cancel')]]
    return sg.Window('Create Address', layout)


def window_destination():
    # Fetch street names from the Address table in your database
    cur.execute('SELECT Street FROM Address')
    rows = cur.fetchall()

    # Extract street names from the query result and put them into a list
    locations = [row[0] for row in rows]
    
    layout = [
        [sg.Text('Destination Information')],
        [sg.Text('Select Start Location:'), sg.DropDown(locations, key='start_location')],
        [sg.Text('Select End Location:'), sg.DropDown(locations, key='end_location')],
        [sg.Button('Confirm')],
    ]
    
    return sg.Window('Destination Window', layout)

def window_payment(passenger_cards):
    card_info = [[f'Name: {card[0]}, Card No: {card[1]}, Type: {card[2]}'] for card in passenger_cards]
    layout = [
        [sg.Text('Select Payment Method:')],
        [sg.Listbox(card_info, size=(60, 6), key='passenger_list')],
        [sg.Button('Approve Payment')],
        
    ]
    return sg.Window('Payment Method', layout)

def button_review_edit():
    # Retrieve all evaluations from the Evaluate table
    cur.execute('SELECT * FROM Evaluate')
    evaluations = cur.fetchall()

    if evaluations:
        # Display the evaluations in a list box for selection
        layout = [[sg.Listbox([f' Trip ID: {evaluation[0]}, Passenger ID: {evaluation[3]}, Comment: {evaluation[1]}, Rating: {evaluation[2]}' for evaluation in evaluations], 
                              size=(60, 20), key='EVAL_LIST')],
                  [sg.Button('Delete Selected Review')]]
        window = sg.Window('Review Edit', layout)

        while True:
            event, values = window.read()
            if event == sg.WINDOW_CLOSED:
                break
            if event == 'Delete Selected Review':
                selected_evaluation = values['EVAL_LIST'][0] if values['EVAL_LIST'] else None
                if selected_evaluation:
                    trip_id = selected_evaluation.split(',')[0].split(':')[1].strip()  # Extract the Trip ID
                    # Delete the selected evaluation from the Evaluate table
                    cur.execute('DELETE FROM Evaluate WHERE Trip_ID = ?', (trip_id,))
                    con.commit()
                    sg.popup('Review deleted successfully.')
                    break
        window.close()
    else:
        sg.popup('No evaluations found.')

def button_confirm_destination(values):
    start_location = values['start_location']
    end_location = values['end_location']
    
    cur.execute('SELECT * FROM Trip_Creation WHERE Driver_ID = ? ORDER BY Trip_ID DESC LIMIT 1', (login_user_id,))
    trip_creation = cur.fetchone()

    if trip_creation:
        trip_id = trip_creation[0]

        # Retrieve the passenger's card information for payment selection
        cur.execute('SELECT Credit_Card.Name_on_Card, Credit_Card.Card_No, Credit_Card.Type FROM User '
                    'INNER JOIN Uploads ON User.User_ID = Uploads.Passenger_ID '
                    'INNER JOIN Credit_Card ON Uploads.Card_No = Credit_Card.Card_No '
                    'WHERE User.User_ID = ?', (trip_creation[1],))
        passenger_cards = cur.fetchall()
        card_info = [[f'Name: {card[0]}, Card No: {card[1]}, Type: {card[2]}'] for card in passenger_cards]
    
    cur.execute('SELECT Location_ID, Street FROM Address')
    rows = cur.fetchall()

    locations = [row[1] for row in rows]

    start_location_mapping = {row[1]: row[0] for row in rows}
    end_location_mapping = {row[1]: row[0] for row in rows}

    if start_location and end_location:
        if start_location not in locations or end_location not in locations:
            sg.popup('Invalid start or end location.')
            return
        
        # Generate a random Trip_ID
        trip_id = random.randint(1000, 9999)
    
        # Get the numeric values for start and end locations
        start = start_location_mapping.get(start_location)
        end = end_location_mapping.get(end_location)
        
        # Calculate the trip distance and fee
        trip_distance = math.sqrt(start ** 2 + end ** 2)
        fee = round(3 * trip_distance, 2)  # Round the fee to 2 decimal places
        
        # Get today's date
        today = datetime.today()
        trip_start_date = today.strftime('%Y-%m-%d')
        
        # Status of the trip initially set to 'Waiting for approval'
        trip_status = 'Waiting for approval'
        
        # Insert a new row into the Trip table with the fee
        cur.execute('INSERT INTO Trip (Trip_ID, Fee, Duration, Trip_Distance, Trip_Start_Date, Trip_Status) VALUES (?, ?, 0, ?, ?, ?)',
                    (trip_id, fee, trip_distance, trip_start_date, trip_status))
        
        # Insert a new row into the Trip_Creation table
        cur.execute('INSERT INTO Trip_Creation (Passenger_ID, Driver_ID, Trip_ID) VALUES (?, ?, ?)',
                    (login_user_id, selected_driver_id, trip_id))
        
        sg.popup('Destination confirmed: {} to {}. Trip created with ID: {}'.format(start_location, end_location, trip_id))

    else:
        sg.popup('Please enter both start and end locations.')

selected_driver_info = None
window = window_login()
def button_your_trips():
    # Retrieve the trips of the logged-in passenger from the Trip_Creation table
    cur.execute('SELECT * FROM Trip_Creation WHERE Passenger_ID = ?', (login_user_id,))
    trip_creations = cur.fetchall()

    if trip_creations:
        trips = []
        for trip_creation in trip_creations:
            trip_id = trip_creation[1]
            cur.execute('SELECT * FROM Trip WHERE Trip_ID = ?', (trip_id,))
            trip = cur.fetchone()
            if trip is not None:
                trips.append(trip)

        if trips:
            # Display the trips in a list box for selection
            layout = [[sg.Listbox([f'Trip ID: {trip[0]}, Date: {trip[4]}, Fee: {trip[1]}, Duration: {trip[2]}, Distance: {trip[3]}, Status: {trip[5]}' for trip in trips], 
                                  size=(60, 20), key='TRIP_LIST')],
                      [sg.Button('Rate Selected Trip')]]
            window = sg.Window('Your Trips', layout)

            while True:
                event, values = window.read()
                if event == sg.WINDOW_CLOSED:
                    break
                if event == 'Rate Selected Trip':
                    selected_trip = values['TRIP_LIST'][0] if values['TRIP_LIST'] else None
                    if selected_trip:
                        trip_id = selected_trip.split(',')[0].split(':')[1].strip()  # Extract the Trip ID
                        layout_rating = [[sg.Text('Comment:'), sg.Input(key='COMMENT')],
                                         [sg.Text('Rating (1-5):'), sg.Input(key='RATING')],
                                         [sg.Button('Submit Rating'), sg.Button('Cancel')]]
                        window_rating = sg.Window('Rate Trip', layout_rating)
                        while True:
                            event_rating, values_rating = window_rating.read()
                            if event_rating in (sg.WINDOW_CLOSED, 'Cancel'):
                                break
                            if event_rating == 'Submit Rating':
                                comment = values_rating['COMMENT']
                                rating = values_rating['RATING']
                                # Insert the comment, rating, and passenger ID into the Evaluate table
                                cur.execute('INSERT INTO Evaluate (Trip_ID, Passenger_ID, Comment, Rating) VALUES (?, ?, ?, ?)', 
                                            (trip_id, login_user_id, comment, rating))
                                con.commit()
                                sg.popup('Rating submitted successfully.')
                                break
                        window_rating.close()
            window.close()
        else:
            sg.popup('No trips found for the passenger.')
    else:
        sg.popup('No trips found for the passenger.')


def button_transactions():
    # Go to the 'Trip_Creation' table, find the matching 'Passenger_ID' to the user's ID
    cur.execute('SELECT * FROM Trip_Creation WHERE Passenger_ID = ?', (login_user_id,))
    trip_creations = cur.fetchall()
    print(trip_creations)
    if trip_creations:
        transaction_info = []
        for trip_creation in trip_creations:
            # Get the 'Trip_ID'
            trip_id = trip_creation[1]

            # Go to the 'Trip' table
            cur.execute('SELECT * FROM Trip WHERE Trip_ID = ?', (trip_id,))
            trip = cur.fetchone()

            # Check the 'Trip_Status'
            if trip is not None and trip[5] == 'Delivered':
                # Store the 'Trip_ID'
                delivered_trip_id = trip[0]

                # Go to the 'Transactions' table and find the matching 'Trip_ID'
                cur.execute('SELECT * FROM Transactions WHERE Trip_ID = ?', (delivered_trip_id,))
                transaction = cur.fetchone()

                if transaction is not None:
                    # Store the 'Payment_ID'
                    payment_id = transaction[1]

                    # Then go to the 'Payment' table
                    cur.execute('SELECT * FROM Payment WHERE Payment_ID = ?', (payment_id,))
                    payment = cur.fetchone()

                    if payment is not None:
                        transaction_info.append(payment)
                        print(transaction_info)

        if transaction_info:
            # Show the matching results
            transaction_info_str = '\n'.join([f'Payment ID: {trans[0]}, Amount: {trans[5]}, Date: {trans[2]}' for trans in transaction_info])
            sg.popup('Your Transactions:\n' + transaction_info_str)
        else:
            sg.popup('No transactions found.')

    else:
        sg.popup('No trips found for the passenger.')

    

while True:
    event, values = window.read()
    if event == 'Login':
        uid = values['id']
        upass = values['password']
        if uid == ADMIN_ID and upass == ADMIN_PASSWORD:
            window.close()
            window = window_admin()
        else:
            button_login(values)
    
    elif event == 'Create Address':
        window.hide()
        window = window_create_address()

    elif event == 'Submit':
        Location_ID = random.randint(1000, 9999)
        Street = values['Street']
        City = values['City']
        Zip_Code = values['Zip_Code']
        X_Cord = values['X_Cord']
        Y_Cord = values['Y_Cord']
        
        cur.execute('''
            INSERT INTO Address (Location_ID, Street, City, Zip_Code, X_Cord, Y_Cord)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (Location_ID, Street, City, Zip_Code, X_Cord, Y_Cord))
        con.commit()
        
        sg.popup('Address created successfully!')
        
        window.close()
        window = window_admin()

    elif event == 'Cancel':
        window.close()
        window = window_admin()
        
    elif event == 'Vehicle Call':
        # Fetch drivers along with their car information and status from the database
        cur.execute('SELECT Driver.Driver_ID, User.Name, Owns_Car.Car_Model, Driver.Status FROM Driver INNER JOIN Owns_Car ON Driver.Driver_ID = Owns_Car.Driver_ID INNER JOIN User ON Driver.Driver_ID = User.User_ID')
        drivers = cur.fetchall()
        
        window.close()
        window = window_vehicle_call(drivers)
        
    elif event == 'Filter':
        car_filter = values['car_filter']
        # Filter drivers based on car model
        if car_filter:
            filtered_drivers = [driver for driver in drivers if car_filter.lower() in str(driver[2]).lower()]
            window.close()
            window = window_vehicle_call(filtered_drivers)
        else:
            window.close()
            window = window_vehicle_call(drivers)
        
            
    elif event == 'Approve Payment':
        
        if selected_driver_id == None:
            sg.popup('No Driver is Selected- No Transaction Made')
        else:    
            selected_drivers =selected_driver_id
            if selected_drivers:
                selected_driver = selected_drivers[0]  # Extract the selected driver from the list

                # Perform the payment process for the selected driver
                # Add your payment code here
                # Show a confirmation message
                sg.popup(f'Payment completed for driver {selected_driver}.')

                # Proceed to destination information
                window.close()
                window = window_destination()

            else:
                sg.popup('Please select a driver.')
            
    elif event == 'Confirm':
        start_location = values['start_location']
        end_location = values['end_location']
        if start_location and end_location:
            # Process the destination information
            # Add your code here
            
            # Show a confirmation message
            sg.popup(f'Destination confirmed: {start_location} to {end_location}.')
        else:
            sg.popup('Please enter both start and end locations.')
        
    elif event == 'Proceed to Payment':
        
    # Fetch logged-in passenger's card information from the database
        cur.execute('SELECT Credit_Card.Name_on_Card, Credit_Card.Card_No, Credit_Card.Type FROM User INNER JOIN Uploads ON User.User_ID = Uploads.Passenger_ID INNER JOIN Credit_Card ON Uploads.Card_No = Credit_Card.Card_No WHERE User.User_ID = ?', (login_user_id,))
        passenger_cards = cur.fetchall()
        selected_drivers = values.get('driver_list', [])
        if selected_drivers:
            selected_driver_info = selected_drivers[0]  # Extract the selected driver info
            if selected_driver_info:
                selected_driver_info = selected_driver_info[0]  # Extract the driver info from the list
                selected_driver_id = selected_driver_info.split(' - ', 1)[0]
                if selected_driver_id == None:
                    sg.popup('No Driver is Selected- No Transaction Made')
                    
                else:
                    print(selected_driver_id)
            else:
                sg.popup('Invalid driver info.')

    # Create the payment window with the passenger's card information
        window.close()
        window = window_payment(passenger_cards)
        
    elif event == 'Toggle Status':
        # Retrieve current status from the Driver table
        cur.execute('SELECT Status FROM Driver WHERE Driver_ID = ?', (login_user_id,))
        current_status = cur.fetchone()[0]
        
        # Toggle the status
        if current_status == 'Available':
            new_status = 'Not Available'
        else:
            new_status = 'Available'
        
        # Update the status in the Driver table
        cur.execute('UPDATE Driver SET Status = ? WHERE Driver_ID = ?', (new_status, login_user_id))
        con.commit()

        sg.popup('Status has been updated to: ' + new_status)
        
    elif event == 'Your Trips':
        button_your_trips()
    elif event == 'Review Edit':
        button_review_edit()    
    elif event == 'Return To Main':
        if login_user_type == 'Passenger':
            window.close()
            window = window_Passenger()
        elif login_user_type == 'Driver':
            window.close()
            window = window_Driver()
        else:
            # this should not happen, bu in case happens let's return to login window
            window.close()
            window = window_login()
    elif event == 'Logout':
        # set login user global parameters
        login_user_id = -1
        login_user_name = -1
        login_user_type = -1
        window.close()
        window = window_login()
    elif event == sg.WIN_CLOSED:
        break
        
    elif event == 'Transactions':
        button_transactions()
        
        
    if event == 'Confirm':
        button_confirm_destination(values)
        # Close the destination window after confirming
        window.close()
        # Open the passenger window
        window = window_passenger()
        
        
    elif event == 'Deliver Passenger':
        button_deliver_passenger()    
        
    elif event == 'View Trips':
    # Retrieve the trips assigned to the driver from the Trip_Creation table
        cur.execute('SELECT * FROM Trip_Creation WHERE Driver_ID = ?', (login_user_id,))
        trip_creations = cur.fetchall()

        if trip_creations:
            trips = []
            for trip_creation in trip_creations:
                trip_id = trip_creation[1]
                cur.execute('SELECT * FROM Trip WHERE Trip_ID = ?', (trip_id,))
                trip = cur.fetchone()
                if trip is not None:
                    trips.append(trip)

            if trips:
                # Display the trips in a listbox
                layout = [
                    [sg.Listbox([f'Trip ID: {trip[0]}, Fee: {trip[1]}, Duration: {trip[2]}, Distance: {trip[3]}, Start Date: {trip[4]}, Status: {trip[5]}' for trip in trips], size=(70, 10), key='trip_list')],
                    [sg.Button('Approve Selected Trip')],
                    [sg.Button('Cancel Selected Trip')]
                ]

                window_trip_list = sg.Window('Your Trips:', layout)

                while True:
                    event_trip_list, values_trip_list = window_trip_list.read()

                    if event_trip_list in (sg.WIN_CLOSED, 'Exit'):
                        break

                    elif event_trip_list == 'Approve Selected Trip':
                        selected_trip_info = values_trip_list['trip_list'][0]
                        selected_trip_id = int(selected_trip_info.split(',')[0].split(':')[1].strip())

                        # Retrieve the status of the selected trip
                        cur.execute('SELECT Trip_Status FROM Trip WHERE Trip_ID = ?', (selected_trip_id,))
                        selected_trip_status = cur.fetchone()[0]

                        if selected_trip_status == 'Waiting for approval':
                            # Update the trip status to 'On the way'
                            cur.execute('UPDATE Trip SET Trip_Status = ? WHERE Trip_ID = ?', ('On the way', selected_trip_id))
                            con.commit()
                            cur.execute('UPDATE Driver SET Status = ? WHERE Driver_ID = ?', ('Not Available', login_user_id))
                            con.commit()
                            sg.popup('Trip approved and status changed to "On the way".')

                            cur.execute('UPDATE Trip SET Trip_Status = ? WHERE Trip_ID = ?', ('Passenger is in the car', selected_trip_id))
                            con.commit()
                            sg.popup('Passenger is in the car.')
                        else:
                            sg.popup('This trip cannot be approved because it is not in "Waiting for approval" status.')
                    
                    
                    elif event_trip_list == 'Cancel Selected Trip':
                        selected_trip_info = values_trip_list['trip_list'][0]
                        selected_trip_id = int(selected_trip_info.split(',')[0].split(':')[1].strip())

                        # Retrieve the status of the selected trip
                        cur.execute('SELECT Trip_Status FROM Trip WHERE Trip_ID = ?', (selected_trip_id,))
                        selected_trip_status = cur.fetchone()[0]

                        if selected_trip_status != 'Completed':
                            # Update the trip status to 'Canceled'
                            cur.execute('UPDATE Trip SET Trip_Status = ? WHERE Trip_ID = ?', ('Canceled', selected_trip_id))
                            con.commit()
                            sg.popup('Trip has been canceled.')
                        else:
                            sg.popup('Completed trips cannot be canceled.')

                    
                    
                    
                    
                    
                    
                window_trip_list.close()

            else:
                sg.popup('No trips found for the driver.')
        else:
            sg.popup('No trips found for the driver.')




    window.close
con.commit()
con.close()






# In[2]:


print(selected_driver_id)


# In[ ]:




