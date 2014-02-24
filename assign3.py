import sys
import cx_Oracle
import random
#import functions
from datetime import datetime, date, time, timedelta

def offerDays(connection, ono):
    resultdict = {}
    
     # COMPILE SQL QUERY
    searchterm = "SELECT ndays FROM offers WHERE ono = '{}'".format(ono)
    
    try:
        curs = connection.cursor()
        curs.execute(searchterm)
        rows = curs.fetchall()

        for i in range(len(rows)):
            resultdict[i] = rows[i]
 
        curs.close()

    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)
        
    return resultdict[0][0]

def promoted(connection, aid):
    resultdict = {}
    daysleft = 0
    
     # COMPILE SQL QUERY
    searchterm = "SELECT * FROM purchases WHERE purchases.aid = '{}'".format(aid)

    try:
        curs = connection.cursor()
        curs.execute(searchterm)
        rows = curs.fetchall()

        for i in range(len(rows)):
            resultdict[i] = rows[i]
            
            # Check expiry
            ndays = offerDays(connection, resultdict[i][3])
            expiresat = resultdict[i][1].date() + timedelta(days=ndays)
            
            # See if expiry date is passed
            today = datetime.today().date()
            if (expiresat - today) > timedelta(days = 0):
                daysleft = expiresat - today
                daysleft = daysleft.days
                
            else: # If ad promotion is expired, return empty resultdict
                print("EXPIRED")
                resultdict = {}
                daysleft = 0

        curs.close()

    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)
    
    return (resultdict, daysleft)


def ownAds(connection, ownemail):
    resultdict = {}
    
     # COMPILE SQL QUERY
    searchterm = "SELECT *\nFROM ads \nWHERE ads.poster = '{}'".format(ownemail)

    try:
        curs = connection.cursor()
        curs.execute(searchterm)
        rows = curs.fetchall()

        for i in range(len(rows)):
            resultdict[i] = rows[i]
 
        curs.close()

    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)

    if len(rows) < 1:
        print("No ads available\n")
        return

    # DISPLAY OPTIONS START
    tick = 0

    for i in range(tick+5):
        tick += 1
        try:

            # Promotion check
            promstate = "Not promoted"
            daysleft = ""
            if promoted(connection, resultdict[i][0])[1] > 0:
                promstate = "Promoted"
                daysleft = promoted(connection, resultdict[i][0])[1]
                

            print(i, resultdict[i][1], resultdict[i][2], resultdict[i][3], resultdict[i][6].date().isoformat(), promstate, daysleft)

        except( IndexError, KeyError):
            pass

    # Start options:
    quit = False
    while not quit:
        userinput = input("\nPlease choose one of the following:\n1: Quit search\n2: Display next 5 ads\n3: Promote ad\n")
        if userinput == '1':
            quit = True
            
        if userinput == '2':
            # Option for displaying next five
            for i in range(tick, tick+5):
                tick += 1
                try:
                    print()
                    print(resultdict[i][1], resultdict[i][2], resultdict[i][3], resultdict[i][6].date().isoformat())
                except (KeyError):
                    break
                continue
                
        if userinput == '3':
            adnocheck = False
            while not adnocheck:
                adno = input("Select ad number to promote: ")
                try:
                    adno = int(adno)
                    adnocheck = True
                except ValueError:
                    print("Please enter a number")

            # Fetch offers
            
            offersdict = {}
    
            # COMPILE SQL QUERY
            searchterm = "SELECT *\nFROM offers"
            
            try:
                curs = connection.cursor()
                curs.execute(searchterm)
                rows = curs.fetchall()

                for i in range(len(rows)):
                    offersdict[i] = rows[i]
                    
                curs.close()
                    
            except cx_Oracle.DatabaseError as err:
                error, = err.args
                print( sys.stderr, "Oracle code:", error.code)
                print( sys.stderr, "Oracle message:", error.message)
            
            try:
                # Check if adno exists
                if resultdict[adno]:
                    # Display offers
                    print("\nSelect an offer by ONO:\n")
                    print("ONO  Duration  Price")
                    for i in offersdict:
                        print(offersdict[i][0],'','','',offersdict[i][1],' ',' ',' ',' ',offersdict[i][2])
                    onoselect = input("\nSelect ONO: ")
                    
                    # Apply promotion
                    applyPromotion(connection, resultdict[adno][0], onoselect)

            except (KeyError, IndexError) as e:
                print("Ad doesn't exist!")


# check to see if the aid is taken
def aidAvailable(connection, aid):
    searchterm = "select * from ads where aid = '{}'".format(aid)

    try:
        curs = connection.cursor()
        curs.execute(searchterm)     
        rows = curs.fetchall()
        curs.close()
        if len(rows)>0:
            print("{} is taken".format(aid))
            return False
        else:
            return True
        
    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)

# checks to see if the pid is taken
def pidAvailable(connection, pid):
    searchterm = "select * from purchases where pur_id = '{}'".format(pid)

    try:
        curs = connection.cursor()
        curs.execute(searchterm)     
        rows = curs.fetchall()
        curs.close()
        if len(rows)>0:
            print("{} is taken".format(pid))
            return False
        else:
            return True
        
    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)




def applyPromotion(connection, aid, ono):
    print("\nAttempting promotion")

    av = False

    while av == False:
        print("Generating PUR_ID")
        randpid = random.randint(100,999)
        pid = "p{}".format(randpid)
        av = pidAvailable(connection, pid)

    print("PUR_ID generated:", pid)

    if av:
        insertterm = "insert into purchases values ('{0}', sysdate, '{1}', {2})".format(pid, aid, ono)
        print("Promoting...")
        try:
            curs = connection.cursor()
            curs.execute(insertterm) 
            connection.commit()
            curs.close()
            print("Promotion successful!")
            
        except cx_Oracle.DatabaseError as err:
            error, = err.args
            print( sys.stderr, "Oracle code:", error.code)
            print( sys.stderr, "Oracle message:", error.message)


def searchUser(connection, email):
    resultsdict = {}
    # Start options:
    quit = False

    while not quit:
        search_method = input("\nPlease choose one of the following:\n1: Quit\n2: Search by user's email address\n3: Search by user's name\n")
        if search_method== '1':
            quit = True
            continue

        # Search by user email
        if search_method == '2':
            resultsdict = {}
            search_email = input("Please enter the user's email\n")
            searchterm = "SELECT name, email, count(aid) FROM users FULL OUTER JOIN ads ON email = poster WHERE email = '{}' GROUP BY name, email".format(search_email)

            try:
                curs = connection.cursor()
                curs.execute(searchterm)
                rows = curs.fetchall()

                for i in range(len(rows)):
                    resultsdict[i] = rows[i]
                    
                curs.close()

                # Handle results
                if len(resultsdict) == 0:
                    print("No results found")
                    continue
                else:
                    print("\nResults:")
                    for i in resultsdict:
                        print(i, resultsdict[i][0])
                    
            except cx_Oracle.DatabaseError as err:
                error, = err.args
                print( sys.stderr, "Oracle code:", error.code)
                print( sys.stderr, "Oracle message:", error.message)

            # Selection options
            select = input("\nWould you like to:\n1: Quit?\n2: Display more details?\n3: Write a review?\n")
            if select == '1':
                quit = True
                continue
            
            if select == '2':
                userno = int(input("Please enter user number: "))
                try:
                    # Fetch AVG RATING
                    avgterm = "SELECT avg(rating) FROM reviews, users WHERE name  = '{}' and email=reviewee".format(resultsdict[userno][0])
                    try:
                        avgdict = {}
                        curs = connection.cursor()
                        curs.execute(avgterm)
                        rows = curs.fetchone()
                        
                        for i in range(len(rows)):
                            avgdict[i] = rows[i]                    
                            
                            curs.close()
                            
                    except cx_Oracle.DatabaseError as err:
                        error, = err.args
                        print( sys.stderr, "Oracle code:", error.code)
                        print( sys.stderr, "Oracle message:", error.message)
                        
                    print()
                    print("Name:", resultsdict[userno][0])
                    print("Email:", resultsdict[userno][1])
                    print("Number of ads:", resultsdict[userno][2])
                    print("Average rating:", avgdict[0])
                except KeyError:
                    print("User doesn't exist")
                    continue

            if select == '3':
                reviewtext = input("Write your review:\n")
                release = False
                while not release:
                    try:
                        rateno = int(input("Give a rating out of 5: "))
                        if rateno>5 or rateno<0:
                            print("Please enter a number between 0 and 5")
                        else:
                            userno = int(input("Please enter user number: "))
                            try:
                                reviewee = resultsdict[userno][1]
                                submitReview(connection, rateno, reviewtext, email, reviewee)
                                release = True
                                     
                            except KeyError:
                                print("User doesn't exist")
                    except ValueError:
                        print("Invalid entry, must enter a number")

            continue

        # Search by user name
        if search_method == '3':
            resultsdict = {}
            search_name = input("\nPlease enter the user's name\n").upper()


            searchterm = "SELECT name, email, count(aid) FROM users FULL OUTER JOIN ads ON email = poster WHERE upper(name) LIKE '%{}%' GROUP BY name, email".format(search_name)


            try:
                curs = connection.cursor()
                curs.execute(searchterm)
                rows = curs.fetchall()
                
                for i in range(len(rows)):
                    resultsdict[i] = rows[i]
                    
                curs.close()
            
                # Handle results
                if len(resultsdict) == 0:
                    print("No results found")
                    continue
                else:
                    print("\nResults:")
                    for i in resultsdict:
                        print(i, resultsdict[i][0])
                
                # Selection options
                select = input("\nWould you like to:\n1: Quit?\n2: Display more details?\n3: Write a review?\n")
                if select == '1':
                    quit = True
                    continue
                if select == '2':
                    userno = int(input("Please enter user number: "))
                    try:
                        # Fetch AVG RATING
                        avgterm = "SELECT avg(rating) FROM reviews, users WHERE name  = '{}' and email=reviewee".format(resultsdict[userno][0])
                        try:
                            avgdict = {}
                            curs = connection.cursor()
                            curs.execute(avgterm)
                            rows = curs.fetchone()
                            
                            for i in range(len(rows)):
                                avgdict[i] = rows[i]                    
                                
                            curs.close()

                        except cx_Oracle.DatabaseError as err:
                            error, = err.args
                            print( sys.stderr, "Oracle code:", error.code)
                            print( sys.stderr, "Oracle message:", error.message)

                        print()
                        print("Name:", resultsdict[userno][0])
                        print("Email:", resultsdict[userno][1])
                        print("Number of ads:", resultsdict[userno][2])
                        print("Average rating:", avgdict[0])
                    except KeyError:
                        print("User doesn't exist")
                    continue
                if select == '3':
                    reviewtext = input("Write your review:\n")
                    release = False
                    while not release:
                        try:
                            rateno = int(input("Give a rating out of 5: "))
                            if rateno>5 or rateno<0:
                                print("Please enter a number between 0 and 5")
                            else:
                                 userno = int(input("Please enter user number: "))
                                 try:
                                     reviewee = resultsdict[userno][1]
                                     submitReview(connection, rateno, reviewtext, email, reviewee)
                                     release = True
                                     
                                 except KeyError:
                                     print("User doesn't exist")
                        except ValueError:
                            print("Invalid entry, must enter a number")
                    
                    continue

                else:
                    print("Invalid choice")

            except cx_Oracle.DatabaseError as err:
                error, = err.args
                print( sys.stderr, "Oracle code:", error.code)
                print( sys.stderr, "Oracle message:", error.message)
        else:
            print("\nPlease try again")
     


def submitReview(connection, rating, text, reviewer, reviewee):

    # Generate rno by adding 1 to the max
    searchterm = "select max(rno) from reviews"
    
    try:
        curs = connection.cursor()
        curs.execute(searchterm)
        rows = curs.fetchone()
        
        rno = int(rows[0])+1
            
        curs.close()

    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)
        
    insertterm = "INSERT into reviews values ({0}, {1}, '{2}', '{3}', '{4}', sysdate)".format(str(rno), str(rating), text, reviewer, reviewee)

    # Start insertion
    try:
        curs = connection.cursor()
        curs.execute(insertterm)
        connection.commit()
        curs.close()
        print("Review posted!")

    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message)


def search(connection, terms):
    resultdict={}
    keywords = []

    for i in range(len(terms)):
        newupper = terms[i].upper()
        keywords.append(newupper)

    # COMPILE SQL QUERY
    searchterm = "SELECT *\nFROM ads \nWHERE upper(ads.title) LIKE '%{0}%' OR upper(ads.descr) LIKE '%{0}%' ".format(keywords[0]) # Always starts with first keyword

        
    # Append LIKE terms for each keyword passed
    # If we have more than one keyword, add the rest in
    if len(keywords)>1:
        for i in range(len(keywords)-1):
            i += 1
            searchterm = searchterm + "OR upper(ads.title) LIKE '%{0}%' OR upper(ads.descr) LIKE '%{0}%' ".format(keywords[i])
    
    # Add ORDER BY to order latest to oldest
    searchterm = searchterm +  "\nORDER BY pdate DESC"

    try:
        curs = connection.cursor()
        curs.execute(searchterm)
        rows = curs.fetchall()

        for i in range(len(rows)):
            resultdict[i] = rows[i]
 
        curs.close()

    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message) 

    # DISPLAY OPTIONS START
    tick = 0
    for i in range(tick+5):
        tick += 1
        try:
            print(i, resultdict[i][0], resultdict[i][1], resultdict[i][2],'' ,'' , '', resultdict[i][3],'' ,'' , '', resultdict[i][4])
        except( IndexError, KeyError):
            pass

    # Start options:
    quit = False
    while not quit:
        userinput = input("\nPlease choose one of the following:\n1: Quit search\n2: Display more details for an ad\n3: Display next 5 ads\n")
        if userinput == '1':
            quit = True
            continue

        if userinput == '2':
            # Option for selecting an ad to display in detail
            selecti = int(input("Choose ad number: "))
            try:
                print()
                print("Ad number:", selecti)
                print("Ad ID:", resultdict[selecti][0])
                print("Type:", resultdict[selecti][1])
                print("Title:", resultdict[selecti][2])
                print("Price:", resultdict[selecti][3])
                print("Description:", resultdict[selecti][4])
                print("Locatoin:", resultdict[selecti][5])
                print("Date:", resultdict[selecti][6].date().isoformat())
                print("Category:", resultdict[selecti][7])
                print("Poster:", resultdict[selecti][8])
            except KeyError:
                print("Ad doesn't exists")
            continue
        
        if userinput == '3':
            # Option for displaying next five
            for i in range(tick, tick+5):
                tick += 1
                try:
                    print()
                    print(i, resultdict[i][0], resultdict[i][1], resultdict[i][2],'' ,'' , '', resultdict[i][3],'' ,'' , '', resultdict[i][4])
                except (KeyError):
                    break
            continue

        else:
            print("\nPlease try again")

def post_ad(connection, email):
    
    # enter the ad_type
    ad_type = input("Select the ad_type.\n1:For Sale\n2:Wanted\n")
    if ad_type == '1':
        ad_type = 'S'
    elif ad_type == '2':
        ad_type = 'W'
    else:
        print("Invalid ad type. Try again.\n")
        return
    # enter the title
    ad_title = input("Enter the title of your ad (20 characters max)\n")
    if len(ad_title) > 20:
        print("Title too long. Try again.\n")
        return
    
    # enter the price
    try:
        ad_price = int(input("Enter the price of your ad. Enter '0' if it is free.\n"))
    except:
        print("Input was not a number. Try again.\n")
        return

    # enter the description
    ad_descr = input("Enter the ad description (40 characters max).\n")
    if len(ad_descr) > 40:
        print("Description too long. Try again.\n")
        return

    # enter the location
    ad_location = input("Enter the ad location (15 characters max)\n")
    if len(ad_location) > 15:
        print("Description too long. Try again.\n")
        return

    # enter the category

    # display category options

    # prepare the query
    catQuery = "SELECT trim(cat) FROM categories"

    cursCat = connection.cursor()
    cursCat.execute(catQuery)
    rows = cursCat.fetchall()
    
    catDict = []
    print("Enter the category to post to.\n")

    for i in range(len(rows)):
        print(rows[i][0])
        catDict.append(rows[i][0])

    print()

    ad_cat = input()
    if ad_cat not in catDict:
        print("Invalid category. Try Again.\n")
        return

    time_tuple = datetime.today().timetuple()
    ad_time = datetime(time_tuple[0], time_tuple[1],time_tuple[2],time_tuple[3],time_tuple[4])

    print("Attempting ad post")

    av = False

    while av == False:
        print("Generating AD_ID")
        randaid = random.randint(100,999)
        aid = "a{}".format(randaid)
        av = aidAvailable(connection, aid)

    print("PUR_ID generated:", aid)

    if av:
        #insertterm = "insert into purchases values ('{0}', sysdate, '{1}', {2})".format(pid, aid, ono)
        print("Posting...")
        try:
            cursAd = connection.cursor()
            
            cursAd.bindarraysize = 1
                
            cursAd.setinputsizes(4, 1, 20, int, 40, 15, datetime, 10, 20)

            data = (aid, ad_type, ad_title, ad_price, ad_descr, ad_location, ad_time, ad_cat, email)

            cursAd.execute("INSERT INTO ADS(AID, ATYPE, TITLE, PRICE, DESCR, LOCATION, PDATE, CAT, POSTER) "
                   "VALUES(:1, :2, :3, :4, :5, :6, :7, :8, :9)",data)
    
            connection.commit()

            cursAd.close()
            print("Post successful!")
            
        except cx_Oracle.DatabaseError as err:
            error, = err.args
            print( sys.stderr, "Oracle code:", error.code)
            print( sys.stderr, "Oracle message:", error.message)

def review_display(connection, email):
    
    # prepare the sql statement
    review = "SELECT rdate, rating, text from reviews, users where reviewee = '{0}' and email = '{0}' and rdate > last_login".format(email)
    
    # create a dictionary to store the results
    reviewDict = {}

    try:
        cursReview = connection.cursor()
        cursReview.execute(review)
        rows = cursReview.fetchall()

        for i in range(len(rows)):
            reviewDict[i] = rows[i]
        #    print(rows[i])
 
        cursReview.close()

    except cx_Oracle.DatabaseError as err:
        error, = err.args
        print( sys.stderr, "Oracle code:", error.code)
        print( sys.stderr, "Oracle message:", error.message) 

    # DISPLAY OPTIONS START
    tick = 0
    print("\nYour reviews since your last login:\n")

    if len(rows) == 0:
        print("No reviews since your last login!")
        return


    for i in range(tick+3):
        tick += 1
        try:
            if reviewDict[i]:
                print("Index:",i) 
                print("Date:", reviewDict[i][0].date().isoformat() )
                print("Rating:", reviewDict[i][1])
                print("Review:", reviewDict[i][2][0:40] )
                print()

        except( IndexError, KeyError):
            pass
        
    # Start options:
    quit = False
    while not quit:
        userinput = input("\nPlease choose one of the following:\n1: Continue\n2: Display more details for a review\n3: Display next 3 reviews\n")
        if userinput == '1':
            quit = True
            continue

        if userinput == '2':
            # Option for selecting an ad to display in detail
            selecti = int(input("Choose review number: "))
            try:
                print()
                print("Ad number:", selecti)
                print("Date:", reviewDict[selecti][0].date().isoformat())
                print("Rating:", reviewDict[selecti][1])
                print("Description:", reviewDict[selecti][2])

            except KeyError:
                print("Ad doesn't exists")
            continue
        
        if userinput == '3':
            # Option for displaying next five
            for i in range(tick, tick+3):
                tick += 1
                try:
                    print()
                    print(i, reviewDict[i][0], reviewDict[i][1], reviewDict[i][2][0:40] )
                except (KeyError):
                    break
            continue

        else:
            print("\nPlease try again")

# if we are running as main do the following:
if __name__=="__main__":

    sql_loop = 1
    while sql_loop == 1:

    # log in to start with your SQL account
        sqlName = input("Please enter your SQL account login name: ")
        sqlPass = input("Please enter your SQL account login password: ")

    # establish the connection to the database

        try:
            connStr = sqlName+'/'+sqlPass+'@gwynne.cs.ualberta.ca:1521/CRS'
            connection = cx_Oracle.connect(connStr)     
            curs = connection.cursor()
            sql_loop = 0
        except:
            print("Invalid Input!")
            quitting = input("Input '0' to quit. Input any other character to try again.")
            if quitting == '0':
                print("Good bye!")
                sys.exit(0)

    # global variables to hold user's log in information
    reg_email = '' 
    reg_pwd = ''
    reg_name = ''

    exit_loop = 0

    # populate the user data table so that we can compare inputs to the DB
    
    while exit_loop == 0:

        # Here is the login screen.
        selection = input("\nPlease select one of the following:\n1: Login\n2: Register\n3: Quit\n")
    
        if selection == '1':
            # handle the login
            user_name = input("Please enter your email address: ")
            user_pass = input("Please enter your password: ")
    
            login = "SELECT trim(email), trim(pwd), trim(name) from users where email = '{0}' and pwd = '{1}'".format(user_name.strip(),user_pass)
            curs.execute(login)
            row = curs.fetchone()
           
            if row is not None:
                
                # convert the row into a list
                row = list(row)

                if row[0]==user_name and row[1]==user_pass:
                    exit_loop = 1
                    reg_email = row[0]
                    reg_pwd = row[1]
                    reg_name = row[2]
                    exit_loop = 1
                    print("Login success! Welcome", reg_name,"\b.")
            else:
                print("Bad credentials. Please try again!")
            
        elif selection == '2':
            # handle registration

            reg_loop = 0
            
            while reg_loop == 0:
                desired_email = input("Please enter your email address for registration (20 character max):\n")
                desired_pass = input("Please enter your desired password (4 character max):\n")
                desired_name = input("Please enter your full name (20 character max):\n")

                if len(desired_email) > 20 or  len(desired_email) < 1 or len(desired_name) > 20 or  len(desired_name) < 1 or len(desired_pass) > 4 or len(desired_pass) < 1:
                    print("Input length invalid (cannot be empty). Please try again")

                else:
                    reg_loop=1
            
            current_date = "SYSDATE"

            # check to see if there is an entry in the database that matches the inputted email address!
            
            check = "SELECT trim(email) from users where email = '{0}'".format(desired_email)
            curs.execute(check)
            row = curs.fetchone()
 
            if row is not None:
                e_name = list(row)
                
                if e_name[0] == desired_email: 
                    print("e-mail address already registered! Please try again!\n")
                else:
                    print("Captain we have a bug!")
            
                # if the email is not registered, register it!            
                
                # maybe throw in a reg exp to ensure that the email address format is valid:
                # i.e. *@*.*
            else:

                cursInsert = connection.cursor()
                cursInsert.bindarraysize = 1
                #cursInsert.setinputsizes(20, 20, 4, datetime.datetime)
                cursInsert.setinputsizes(20, 20, 4, datetime)
                # the data to be passed to the database
                
                time_tuple = datetime.today().timetuple()
                insert_time = datetime(time_tuple[0], time_tuple[1],time_tuple[2],time_tuple[3],time_tuple[4])
                
                data = (desired_email, desired_name, desired_pass, insert_time)
                            
                cursInsert.execute("INSERT INTO USERS(EMAIL, NAME, PWD, LAST_LOGIN) VALUES(:1, :2, :3, :4)",data)
                connection.commit()
                                
                # now go back to login is it is successfull
                print("Registration successful!\n")

        elif selection == '3':    
            
            print("Goodbye!")
            # close your connection
            connection.close()
            # exit the program
            sys.exit(0)
        else:
            print("Invalid selection! Please try again.\n")

    fresh_login = 1
    logged_in = 1
    while logged_in==1:

        # display three reviews at a time and at most 40 chars from the description
        if fresh_login == 1:
            review_display(connection, reg_email)
            fresh_login = 0
        

        print("\nPlease select one of the following options:")
        login_selection = input("1: Search for ads\n2: List own ads\n3: Search for users\n4: Post an ad\n5: Logout\n")
        
        if login_selection == '1':
            keywords = input("Enter the keywords you would like to search for.\nSeperate the search terms with a space:\n")
            # split up the keywords into a list
            keywords = keywords.split()
            
            # call the search function
            search(connection, keywords)

        elif login_selection == '2':    
            # list your own ads
            ownAds(connection, reg_email)

        elif login_selection == '3':
            # user search function call
            searchUser(connection, reg_email)

        elif login_selection == '4':
            # call the post ad function
            post_ad(connection, reg_email)

        elif login_selection == '5':
            print("Goodbye", reg_name,"\b!")

            # Make sure to update the logout time. Should be like the log in
            cursUpdate = connection.cursor()

            # time_tuple = datetime.today().timetuple()
            # insert_time = datetime(time_tuple[0], time_tuple[1],time_tuple[2],time_tuple[3],time_tuple[4])
            
            time_update = "UPDATE users SET LAST_LOGIN = (select SYSDATE from dual)  WHERE email = '{0}'".format(reg_email)

            cursUpdate.execute(time_update)
                  
            connection.commit()
            # close your connection
            connection.close()
       
            # exit the program
            sys.exit(0)
    
        else:
            print("Invalid selection! Please try again.\n")

