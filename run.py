DEBUG = False

TO_EXE = not __file__.endswith('.py')

XRESOLUTION = 1920

import struct, pygame, sys,  os, stockfish, pickle, subprocess
import time as tt
from datetime import datetime, time, timedelta
from pygame.locals import *
from socket import *
from select import * 
from Chessnut import Game
import codes
import chess
import chess.pgn

stockfish.TO_EXE = TO_EXE

def txt ( s, x, y, color ):
    img = font.render( s, 22, color) # string, blend, color, background color
    pos = x*x_multiplier,y*y_multiplier
    scr.blit( img, pos )

def txt_large ( s, x, y, color ):
    img = font_large.render( s, 22, color) # string, blend, color, background color
    pos = x*x_multiplier,y*y_multiplier
    scr.blit( img, pos )

def do_poweroff( proc ):
    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)])
    pygame.display.quit()
    pygame.quit()
    sys.exit()

    
f=open('screen.ini','rb')
try:
    XRESOLUTION = int( f.readline().split(" #")[0] )
    print XRESOLUTION
    if XRESOLUTION==1380: XRESOLUTION=1366
except:
    print "Cannot read resolution from screen.ini"
if XRESOLUTION!=480 and XRESOLUTION!=1366 and XRESOLUTION!=1920:
    print "Wrong value xscreensize.ini =",XRESOLUTION,", setting 1366"
    XRESOLUTION = 1366
try:
    s = f.readline().split(" #")[0]
    if s=='fullscreen': fullscreen=True
    else: fullscreen=False
except:
    fullscreen=False
    print "Cannot read 'fullscreen' or 'window' as second line from screen.ini"
f.close()

    
# define set of colors
green = 0, 200, 0
red   = 200, 0, 0
black = 0,0,0
blue = 0, 0, 200
white = 255,255,255
terminal_text_color = 0xcf, 0xe0, 0x9a
grey = 100, 100, 100
lightgrey = 190, 190, 190
lightestgrey = 230, 230, 230

if TO_EXE: usb_proc = subprocess.Popen("usb.exe", shell=True)
else: usb_proc = subprocess.Popen("python usb.py", shell=True)

tt.sleep(1) # time to make stable COMx connection


os.environ['SDL_VIDEO_WINDOW_POS'] = "90,20"
pygame.init()

# auto reduce a screen's resolution
infoObject = pygame.display.Info()
xmax, ymax = infoObject.current_w, infoObject.current_h
print "Xmax=",xmax
print "XRESOLUTION =",XRESOLUTION
if xmax<XRESOLUTION: XRESOLUTION=1366
if xmax<XRESOLUTION: XRESOLUTION=480

if XRESOLUTION==480: screen_width, screen_height = 480, 320
elif XRESOLUTION==1920: screen_width, screen_height = 1500, 1000
elif XRESOLUTION==1366: screen_width, screen_height = 900, 600
x_multiplier, y_multiplier = float(screen_width)/480, float(screen_height)/320

if fullscreen:
    scr = pygame.display.set_mode( (screen_width, screen_height), pygame.HWSURFACE | pygame.DOUBLEBUF |pygame.FULLSCREEN, 32 )
else:
    scr = pygame.display.set_mode( (screen_width, screen_height), pygame.HWSURFACE | pygame.DOUBLEBUF, 32 )

    
pygame.display.set_caption('Chess software')
font = pygame.font.Font( "Fonts//OpenSans-Regular.ttf", int(13*y_multiplier) )
font_large = pygame.font.Font( "Fonts//OpenSans-Regular.ttf", int(19*y_multiplier) )

scr.fill( black ) # clear screen
pygame.display.flip() # copy to screen

# change mouse cursor to be unvisible - not needed for Windows!
#if not DEBUG:
#    mc_strings = '        ','        ','        ','        ','        ','        ','        ','        '
#    cursor,mask = pygame.cursors.compile( mc_strings )
#    cursor_sizer = ((8, 8), (0, 0), cursor, mask)
#    pygame.mouse.set_cursor(*cursor_sizer)

#----------- load sprites
names = "black_bishop", "black_king", "black_knight", "black_pawn", "black_queen", "black_rook",\
    "white_bishop", "white_king", "white_knight","white_pawn","white_queen","white_rook","terminal",\
    "logo",  "chessboard_xy",  "new_game", "resume_game", "save",  "exit", "hint", "setup",\
    "take_back", "resume_back",\
"analysing", "back", "black", "confirm", "delete-game", "depth1", "depth2", "depth3", "depth4",\
 "depth5", "depth6", "depth7", "depth8", "depth9", "depth10", "depth11", "depth12", "depth13",\
 "depth14", "depth15", "depth16", "depth17", "depth18", "depth19", "depth20", "done",\
 "force-move",  "select-depth", "start", "welcome", "white", "hide_back", "start-up-logo",\
"do-your-move", "move-certabo", "place-pieces", "place-pieces-on-chessboard", "new-setup",\
"please-wait", "check-mate-banner"
 
sprite = {}
for name in names:
    if XRESOLUTION==480: path='sprites//'
    elif XRESOLUTION==1920: path='sprites_1920//'
    elif XRESOLUTION==1366: path='sprites_1380//'
    sprite[ name ] = pygame.image.load(path+name+'.png')
    
    
# show sprite by name from names
def show( name, x, y ):
    scr.blit( sprite[name], (x*x_multiplier,y*y_multiplier) )



# Show chessboard using FEN string like 
# "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FEN = {"b": "black_bishop", "k":"black_king", "n":"black_knight", "p":"black_pawn",\
        "q":"black_queen", "r":"black_rook", "B":"white_bishop", "K":"white_king",\
        "N":"white_knight","P":"white_pawn","Q":"white_queen", "R":"white_rook" }

def show_board( FEN_string, x0, y0 ):
    show("chessboard_xy", x0, y0 )

    x,y = 0,0
    for c in FEN_string:
        if c in FEN:
            show( FEN[c], x0+26+31.8*x, y0+23+y*31.8 )
            x+=1
        elif c=="/": # new line
            x=0
            y+=1
        elif c==" ":
            break
        else:
            x+=int(c)    


letter = "a","b","c","d","e","f","g","h"

def show_board_and_animated_move( FEN_string, move, x0, y0 ):
    piece = ""

    xa = letter.index( move[0] )
    ya = 8-int( move[1] )
    xb = letter.index( move[2] )
    yb = 8-int( move[3] )
    xstart, ystart = x0+26+31.8*xa, y0+23+ya*31.8
    xend, yend = x0+26+31.8*xb, y0+23+yb*31.8
    
    show("chessboard_xy", x0, y0 )
    x,y = 0,0
    for c in FEN_string:

        if c in FEN:
            if x!=xa or y!=ya:
                show( FEN[c], x0+26+31.8*x, y0+23+y*31.8 )
            else:
                piece = FEN[c]
            x+=1
        elif c=="/": # new line
            x=0
            y+=1
        elif c==" ":
            break
        else:
            x+=int(c)    
    #pygame.display.flip() # copy to screen
    if piece=="":
        return 
    print piece   
    for i in range(20):
        x,y = 0,0
        show("chessboard_xy", x0, y0 )
        for c in FEN_string:
            if c in FEN:
                if x!=xa or y!=ya:
                    show( FEN[c], x0+26+31.8*x, y0+23+y*31.8 )
                x+=1
            elif c=="/": # new line
                x=0
                y+=1
            elif c==" ":
                break
            else:
                x+=int(c)    

        xp = xstart + (xend-xstart)*i/20.0                
        yp = ystart + (yend-ystart)*i/20.0                
        show( piece, xp, yp )
        #print x,y
        #tt.sleep(0.1)
        pygame.display.flip() # copy to screen
        tt.sleep(0.01)
        
        
#------------- start point --------------------------------------------------------

timeout = datetime.now() + timedelta( milliseconds = 500 )

old_left_click = 0

T = datetime.now() + timedelta( milliseconds = 100 )
x,y=0,0

window = "home" # name of current page
dialog = "" # dialog inside the window
#window="resume"

timer = 0
play_white = True
difficulty = 0
board_state = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
terminal_text="Game started"
terminal_text_line2="Terminal text here"
pressed_key = ""
hint_text = ""
move_history = []
board_history = []
name_to_save = ""

board_letters = "a", "b", "c", "d", "e", "f", "g", "h"
previous_board_click = "" # example: "e2"
board_click = "" # example: "e2"
do_ai_move = True
do_user_move = False
conversion_dialog = False
mate_we_lost = False
mate_we_won = False

renew = True
left_click = False

saved_files = []
resume_file_selected = 0
resume_file_start = 0 # starting filename to show

KUDA_POSYLAT = ('127.0.0.1', 3002) # send to
NASH_ADRES =   ('127.0.0.1', 3003) # listen to
sock = socket(AF_INET, SOCK_DGRAM)
sock.setsockopt( SOL_SOCKET,SO_REUSEADDR, 1 )
sock.bind( NASH_ADRES )
sock.setsockopt( SOL_SOCKET,SO_BROADCAST, 1 )
recv_list = [ sock ]
new_usb_data = False
usb_data_exist = False

codes.load_calibration()
calibration = False
calibration_samples_counter = 0
calibration_samples = []

usb_data_history_depth = 5
usb_data_history = range(usb_data_history_depth)
usb_data_history_filled = False
usb_data_history_i = 0

banner_right_places = False
banners_counter = 0
game_process_just_startted = True
banner_do_move = False

new_setup = False

#sock.sendto( chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0), KUDA_POSYLAT )
message = chr(0xFF)+chr(0xFF)+chr(0xFF)+chr(0xFF)+chr(0xFF)+chr(0xFF)+chr(0xFF)+chr(0xFF)
sock.sendto( message, KUDA_POSYLAT )

scr.fill( white ) # clear screen
show( "start-up-logo",7,0 )
pygame.display.flip() # copy to screen
tt.sleep(2)
sock.sendto( chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0), KUDA_POSYLAT )

poweroff_time = datetime.now()

while 1:
    t = datetime.now() # current time

    # event from system & keyboard
    for event in pygame.event.get(): # all values in event list
        if event.type == pygame.QUIT:
            do_poweroff( usb_proc )
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                do_poweroff( usb_proc )
            if event.key == pygame.K_h:
                window = "home"
            if event.key == pygame.K_a:
                pass

    recv_ready, wtp, xtp = select( recv_list, [], [], 0.002 )

    if recv_ready:
        try:
            data, addr = sock.recvfrom( 2048 )
            usb_data = map( int, data.split(" ") )
            new_usb_data = True
            usb_data_exist = True
            
        except:
            print "No new data from usb.exe, perhaps chess board not connected"

    scr.fill( white ) # clear screen

    x,y   = pygame.mouse.get_pos() # mouse position
    x = x/x_multiplier;
    y = y/y_multiplier;
    
    mbutton = pygame.mouse.get_pressed()
    if DEBUG: txt ( str((x,y)), 80,300, lightgrey )
    if mbutton[0]==1 and old_left_click==0:
        left_click = True
    else: left_click = False

    
    if x<110 and y<101 and mbutton[0]==1:
        if datetime.now()-poweroff_time >= timedelta( seconds = 2 ): do_poweroff(usb_proc)
    else:
        poweroff_time = datetime.now()    


    show( "logo", 8,6 )
    #-------------- home ----------------
    if window=="home":

        if new_usb_data:
            new_usb_data = False

            if usb_data_history_i >= usb_data_history_depth:
                usb_data_history_filled = True
                usb_data_history_i = 0    

            if DEBUG: print "usb_data_history_i = ",usb_data_history_i
            usb_data_history[ usb_data_history_i ] = usb_data[:]
            usb_data_history_i += 1    
            if usb_data_history_filled:
                usb_data_processed = codes.statistic_processing( usb_data_history, False )
                if usb_data_processed != []:
                    test_state = codes.usb_data_to_FEN( usb_data_processed )                
                    if test_state != "":
                        board_state = test_state
                else:
                    print "Statistic processing failed, found unknown piece"
                
            if calibration:
                calibration_samples.append( usb_data )
                print "    adding new calibration sample"
                calibration_samples_counter += 1
                if calibration_samples_counter>=15:
                    print "------- we have collected enough samples for averaging ----"
                    usb_data = codes.statistic_processing_for_calibration( calibration_samples, False )
                    #print usb_data
                    codes.calibration( usb_data, new_setup )
                    board_state = codes.usb_data_to_FEN( usb_data )
                    calibration = False    


            # "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            # do a calibration
        show( "new_game", 5, 149 )
        show( "resume_game", 5, 149 +40)
        show( "setup", 5, 149+80 )
        show( "new-setup", 5, 149+120 )

        show_board( board_state, 178, 40)
        show( "welcome",111,6 )

        if calibration:
            show( "please-wait",253,170 )

        if left_click:
                
            if 6<x<102 and 232<y<265:
                print "calibration"
                if usb_data_exist:
                    calibration = True
                    new_setup = False
                    calibration_samples_counter = 0
                    calibration_samples = []
                    calibration_samples.append( usb_data )
            if 6<x<102 and y>=265:
                print "New setup calibration"
                if usb_data_exist:
                    calibration = True
                    new_setup = True
                    calibration_samples_counter = 0
                    calibration_samples = []
                    calibration_samples.append( usb_data )

            if 6<x<123 and 150<y<190: # new game pressed
                window="new game"
                sock.sendto( chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0), KUDA_POSYLAT ) # switch off LEDs

            if 6<x<163 and 191<y<222: # resume pressed
                window="resume"
                # update saved files list to load
                files = os.listdir(".")
                saved_files = [v for v in files if '.sav' in v]
                saved_files_time = []
                terminal_text=""
                terminal_text_line2=""
                mate_we_won = False
                mate_we_lost = False

                for name in saved_files:
                    saved_files_time.append( tt.gmtime( os.stat(name).st_mtime ) )

    #---------------- Resume game dialog ----------------
    elif window=="resume":
        txt_large( "Select game name to resume",159,1,black ) 
        show( "resume_back", 107,34 )
        show( "resume_game", 263,283 )
        show( "back", 3, 146)
        show( "delete-game", 103, 283)

        pygame.draw.rect(scr, lightestgrey, \
          (113*x_multiplier, 41*y_multiplier+resume_file_selected*29*y_multiplier,\
          330*x_multiplier,30*y_multiplier) ) # selection

        for i in range( len(saved_files) ):
            if i>7: break
            txt_large( saved_files[i + resume_file_start].replace('.sav',''), 117, 41+i*29 , grey )
            v = saved_files_time[i]

            txt_large( "%d-%d-%d  %d:%d"%(v.tm_year, v.tm_mon, v.tm_mday, v.tm_hour, v.tm_min),\
                            300, 41+i*29 , lightgrey )

        if dialog == "delete":
            show( "hide_back",0, 0 )
            
            pygame.draw.rect(scr, lightgrey, (200+2, 77+2,220,78) )
            pygame.draw.rect(scr, white, (200, 77,220,78) )
            txt_large("Delete the game ?",200+32,67+15,grey)
            show( "back", 200+4, 77+40 )
            show( "confirm", 200+4+112, 77+40 )

            if left_click:
                if (77+40-5)<y<(77+40+30):
                    dialog = ""
                    if x>(200+105): # confirm button
                        print "do delete"
                        os.system("del "+saved_files[ resume_file_selected + resume_file_start ])
                        # update saved files list to load
        
                        files = os.listdir(r"")
                        saved_files = [v for v in files if '.sav' in v]
                        saved_files_time = []
                        for name in saved_files:
                            saved_files_time.append( tt.gmtime( os.stat(name).st_mtime ) )

                        resume_file_selected=0
                        resume_file_start=0

            
        if left_click:

            if 7<x<99 and 150<y<179: # back button
                window = "home"

            if 106<x<260 and 287<y<317: # delete button
                dialog = "delete" # start delete confirm dialog on the page

            if 107<x<442 and 40<y<274: # pressed on file list
                i = (int(y)-41)/29
                if i< len(saved_files):
                    resume_file_selected = i
            
            if 266<x<422 and 286<y<316: # Resume button
                f = open( saved_files[ resume_file_selected + resume_file_start ], 'rb' )
                move_history, board_state, terminal_text, terminal_text_line2, board_history, timer,\
                     play_white, difficulty = pickle.load(f)
                f.close()
                game_engine = stockfish.ini(difficulty)
                previous_board_click=""
                board_click=""
                do_ai_move = False
                do_user_move = False
                conversion_dialog = False
                banner_do_move = False
                banner_place_pieces = True

                window = "game"    
            if 448<x<472: # arrows
                if 37<y<60: # arrow up
                    if resume_file_start>0:
                        resume_file_start-=1
                elif 253<y<284:
                    if (resume_file_start+8)<len(saved_files):
                        resume_file_start+=1
                

    #---------------- Save game dialog ----------------
    elif window=="save":

        txt_large( "Enter game name to save",159,41,grey )         
        show( "terminal",139,80 )
        txt_large( name_to_save,273-len(name_to_save)*(51/10.0),86,terminal_text_color )

        # show keyboard        
        keyboard_buttons = ('1','2','3','4','5','6','7','8','9','0','-'),\
                           ('q','w','e','r','t','y','u','i','o','p'),\
                           ('a','s','d','f','g','h','j','k','l'),\
                           ('z','x','c','v','b','n','m')

        lenx = 42 # size of buttons
        leny = 38 # size of buttons
        
        ky = 128
        x0 = 11
        
        hover_key = ""

        pygame.draw.rect(scr, lightgrey, (431*x_multiplier, 81*y_multiplier,lenx*x_multiplier-2,leny*y_multiplier-2) ) # back space
        txt_large("<", (431+14),(81+4), black)

        for row in keyboard_buttons:
            kx = x0
            for key in row:
                pygame.draw.rect(scr, lightgrey, (kx*x_multiplier, ky*y_multiplier,lenx*x_multiplier-2,leny*y_multiplier-2) )
                txt_large(key, kx+14,ky+4, black)
                if kx<x<(kx+lenx) and ky<y<(ky+leny):
                    hover_key = key
                kx += lenx
            ky +=leny
            x0+=20
        
        pygame.draw.rect(scr, lightgrey, (x0*x_multiplier+lenx*x_multiplier, ky*y_multiplier,188*x_multiplier,leny*y_multiplier-2) ) #spacebar
        if (x0+lenx)<x<(x0+lenx+188) and ky<y<(ky+leny):
            hover_key = " "
        show("save", 388, 264 )
        if 388<x<(388+100) and 263<y<(263+30):
            hover_key = "save"
        if 431 <x< (431+lenx) and 81<y<(81+leny):
            hover_key = "<"    

        # ----- process buttons -----
        if left_click:

            if hover_key!="":
                if hover_key == "save":
                    f = open(name_to_save+".sav", 'wb')
                    pickle.dump( [ move_history, board_state, terminal_text, terminal_text_line2, board_history,\
                                     timer, play_white, difficulty], f)
                    f.close()
                    if move_history:
                        game = chess.pgn.Game()
                        game.headers['Date'] = datetime.now().strftime('%Y.%m.%d')
                        if play_white:
                            game.headers['White'] = 'Human'
                            game.headers['Black'] = 'Computer'
                        else:
                            game.headers['White'] = 'Computer'
                            game.headers['Black'] = 'Human'
                        if mate_we_lost:
                            game.headers['Result'] = '0-1' if play_white else '1-0'
                        if mate_we_won:
                            game.headers['Result'] = '1-0' if play_white else '0-1'
                        node = game.add_variation(chess.Move.from_uci(move_history[0]))
                        for move in move_history[1:]:
                            node = node.add_variation(chess.Move.from_uci(move))
                        with open('{}.pgn', 'w') as f:
                            exporter = chess.pgn.FileExporter(f)
                            game.accept(exporter)
                    window = "game"
                    #banner_do_move = False
                    previous_board_click=""
                    board_click=""
                    left_click = False
                    conversion_dialog = False


                elif hover_key == "<":
                    if len(name_to_save)>0:
                        name_to_save = name_to_save[ :len(name_to_save)-1 ]
                else:
                    if len(name_to_save)<22:
                        name_to_save += hover_key
            
    #---------------- game dialog ----------------
    elif window=="game":

        if new_usb_data:
            new_usb_data = False
            if DEBUG: print "Virtual board: ",board_state

            banners_counter +=1

            if usb_data_history_i >= usb_data_history_depth:
                usb_data_history_filled = True
                usb_data_history_i = 0    

            #print "usb_data_history_i = ",usb_data_history_i
            usb_data_history[ usb_data_history_i ] = usb_data[:]
            usb_data_history_i += 1    
            if usb_data_history_filled:
                usb_data_processed = codes.statistic_processing( usb_data_history, False )
                if usb_data_processed != []:
                    test_state = codes.usb_data_to_FEN( usb_data_processed )                
                    if test_state != "":
                        board_state_usb = test_state
                        game_process_just_started = False


                        # compare virtual board state and state from usb
                        s1 = board_state.split(' ')[0]
                        s2 = board_state_usb.split(' ')[0]
                        if s1!=s2:
                            if banner_do_move:
                                move = codes.FENs2move( board_state, board_state_usb, play_white )
                                if move!="":
                                    banner_do_move = False
                                    do_user_move = True
                            else:
                                if DEBUG: print "Place pieces on their places"
                                banner_right_places = True
                        else:
                            if DEBUG: print "All pieces on right places"
                            sock.sendto( chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0)+chr(0), KUDA_POSYLAT )
                            banner_right_places = False
                            
                            # start with black, do move just right after right initial board placement
                            if banner_place_pieces and not play_white:
                                do_ai_move = True
                                banner_place_pieces = False
                                
                            if not game_process_just_started and not do_user_move and not do_ai_move:
                                banner_place_pieces = False
                                banner_do_move = True
                else:
                    print "Statistic processing failed, found unknown piece"



        show( "terminal",179,3 )

        txt ( terminal_text, 183,18, terminal_text_color )
        txt ( terminal_text_line2, 183,3, terminal_text_color )
        txt_large( hint_text, 96, 185+22, grey )
    
        # buttons
        show( "take_back", 5, 140+22 )
        show( "hint", 5, 140+40+22   )
        show( "save", 5, 140+100 )
        show( "exit", 5, 140+140 )

        if dialog == "exit":
            show_board( board_state, 178, 40)
            pygame.draw.rect(scr, lightgrey, (229*x_multiplier, 79*y_multiplier,200*x_multiplier,78*y_multiplier) )
            pygame.draw.rect(scr, white, (227*x_multiplier, 77*y_multiplier,200*x_multiplier,78*y_multiplier) )
            txt("Save the game or not ?",227+37,77+15,grey)
            show( "save", 238, 77+40 )
            show( "exit", 238+112, 77+40 )

            if left_click:
                if (77+40-5)<y<(77+40+30):
                    if x>(238+105): # exit button
                        dialog = ""
                        window = "home"
                        board_state = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
                        terminal_text=""
                        terminal_text_line2=""
                        pressed_key = ""
                        hint_text = ""
                        move_history = []
                        board_history = []
                        previous_board_click = "" # example: "e2"
                        board_click = "" # example: "e2"
                    else: # save button
                        dialog = ""
                        window = "save"
                        previous_board_click=""
                        board_click=""


        else: # usual game process
            if do_ai_move and ( not mate_we_won and not mate_we_lost ):
                do_ai_move = False

                # stockfish chess engine interrogation
#                show_board( board_state, 178, 40)
#                show("analysing", 277, 160 )
#                pygame.display.flip() # copy to screen

                #game_engine.setposition( move_history )
                #print "AI move..."

#                ai_move = game_engine.bestmove()['move']

                proc = stockfish.start_thinking_about_bestmove( move_history, difficulty )
                #print "continues..."

                show_board( board_state, 178, 40)
                pygame.draw.rect(scr, lightgrey, (229*x_multiplier, 79*y_multiplier,200*x_multiplier,78*y_multiplier) )
                pygame.draw.rect(scr, white, (227*x_multiplier, 77*y_multiplier,200*x_multiplier,78*y_multiplier) )
                txt_large("Analysing...",227+55,77+8,grey)
                show( "force-move", 247, 77+39 )
                pygame.display.flip() # copy to screen

                got_fast_result = False
                #while stockfish.th.is_alive(): # thinking
                while proc.poll()==None:
                
                    # event from system & keyboard
                    for event in pygame.event.get(): # all values in event list
                        if event.type == pygame.QUIT:
                            pygame.display.quit()
                            pygame.quit()
                            sys.exit()

                    x,y   = pygame.mouse.get_pos() # mouse position
                    x = x/x_multiplier;
                    y = y/y_multiplier;

                    mbutton = pygame.mouse.get_pressed()

                    #txt_large("%d %d %s"%(x,y,str(mbutton)),0,0,black)
                    #pygame.display.flip() # copy to screen
                    if mbutton[0]==1 and 249<x<404 and 120<y<149: # pressed Force move button
                        print "------------------------------------"
                        ai_move = stockfish.get_fast_result( move_history )
                        got_fast_result = True
                        break
                    
                    tt.sleep(0.05)


                if not got_fast_result:
                    ai_move = stockfish.get_result_of_thinking()
                

                print "AI move: ", ai_move

                # highlight right LED
                i,value, i_source, value_source = codes.move2led( ai_move ) # error here if checkmate before
                message = ""
                for j in range(8):
                    if j!=i and j!=i_source:
                        message += chr(0)
                    elif j==i and j==i_source:
                        message += chr( value+value_source )
                    elif j==i: 
                        message += chr( value )
                    else:
                        message += chr( value_source )


                sock.sendto( message, KUDA_POSYLAT )
                #banner_do_move = True
                show_board_and_animated_move( board_state, ai_move, 178, 40 )

                if play_white:
                    terminal_text += ", black move: "+ai_move
                else:
                    terminal_text_line2 = terminal_text
                    terminal_text = "white move: "+ai_move

                try:
                    chessgame = Game( fen = board_state )
                    chessgame.apply_move( ai_move ) # validate move
                    move_history.append(  ai_move )
                    board_state = str(chessgame)
                    print "   stockfish move: ",ai_move
                    print "after stockfish move: ", board_state
                    board_history.append( board_state )
                except:
                    print "   ----invalid chess_engine move! ---- ",ai_move
                    terminal_text = ai_move+" - invalid move !"

                print "\n\n",board_state


                # check for mate
                mate_we_lost = False
                chessgame = Game( fen = board_state )
                possible_moves = chessgame.get_moves()

                #print "state = ",chessgame.status
                #print "possible moves after AI move: ",possible_moves

                if chessgame.status==chessgame.CHECK:
                    #print " *************** check ! ******************"
                    terminal_text += " check!"

                #if len(possible_moves)==0:
                if chessgame.status>=chessgame.CHECKMATE:
                    print "mate!"
                    mate_we_lost = True 


            # user move
            if do_user_move and ( not mate_we_won and not mate_we_lost ) :
                do_user_move = False
                try:
                    chessgame = Game( fen = board_state )
                    chessgame.apply_move(move) # validation
                    move_history.append(move)

                    board_state = str(chessgame)
                    board_history.append( board_state )

                    #codes.FENs2move( board_history[ len(board_history)-2 ], board_state, play_white )
#                if play_white:
 #                   terminal_text += ", black move: "+ai_move
 #               else:
 #                   terminal_text_line2 = terminal_text
 #                   terminal_text = "white move: "+ai_move

                    print "   user move: ",move
                    do_ai_move = True
                    hint_text = ""
                    if play_white:
                        terminal_text_line2 = terminal_text
                        terminal_text = "white move: "+move
                    else:
                        terminal_text += ", black move: "+move

                except:
                    print "   ----invalid user move! ---- ",move
                    terminal_text_line2 = terminal_text

                    terminal_text = move+" - invalid move !"
                    previous_board_click = ""
                    board_click = ""
                    banner_do_move = True

                # check for mate
                mate_we_won = False
                chessgame = Game( fen = board_state )
                possible_moves = chessgame.get_moves()
                #print "state = ",chessgame.status
                #print "possible moves after AI move: ",possible_moves

                if chessgame.status==chessgame.CHECK:
                    #print " *************** check ! ******************"
                    terminal_text += " check!"

    #            if len(possible_moves)==0:
                if chessgame.status>=chessgame.CHECKMATE:
                    print "mate! we won!"
                    mate_we_won = True 

            show_board( board_state, 178, 40)

            # -------------------- show banners -------------------------
#            if banners_counter%2 ==0:
            x0, y0 = 5,127
            if banner_right_places:
                if move_history == [] or banner_place_pieces:
                    show( "place-pieces", x0+2, y0+2 )
                else:
                    show( "move-certabo", x0, y0+2 )
#                pygame.draw.rect(scr, black, (x0+2, y0+2, 167, 28) )
#                txt("Please place pieces",x0+5+22,y0+4,white)
            if banner_do_move:
                show( "do-your-move", x0+2, y0+2 )
                #pygame.draw.rect(scr, black, (x0+2, y0+2, 167, 28) )
                #txt("Please move your piece",x0+14,y0+4,white)


            if mate_we_lost or mate_we_won:
                show( "check-mate-banner", 227, 97 )
                #pygame.draw.rect(scr, lightgrey, (227+2, 77+2,200,78) )
                #pygame.draw.rect(scr, white, (227, 77,200,78) )
                #txt_large("Mate! Game Over",227+21,77+21,grey)


            if conversion_dialog:
                pygame.draw.rect(scr, lightgrey, (227+2, 77+2,200,78) )
                pygame.draw.rect(scr, white, (227, 77,200,78) )
                txt("Select conversion to:",227+37,77+7,grey)
                if play_white: # show four icons
                    icons = "white_bishop", "white_knight", "white_queen", "white_rook"
                    icon_codes = "B", "N", "Q", "R"
                else:
                    icons = "black_bishop", "black_knight", "black_queen", "black_rook"
                    icon_codes = "b", "n", "q", "r"
                i=0
                for icon in icons:
                    show( icon, 227+15+i, 77+33 )
                    i+=50


            if left_click:
                if conversion_dialog:
                    if (227+15)<x<(424) and (77+33)<y<(77+33+30):
                        i = (x-(227+15-15))/50
                        if i<0: i=0
                        if i>3: i=3
                        icon = icon_codes[ i ]
                        if len(move)==4:
                            move += icon
                            print "move for conversion: ", move
                            conversion_dialog = False
                            do_user_move = True
                else:

                    if 6<x<123 and (140+140)<y<(140+140+40): # Exit button
                        dialog = "exit" # start dialog inside Game page

                    if 6<x<127 and (143+22)<y<(174+22): # Take back button
                        if len(board_history)>2:
                            print "--------- before take back: "
                            print board_history
                            print move_history

                            board_history.pop() # remove last element
                            board_history.pop() # remove last element
                            board_state = board_history[ len(board_history)-1 ]
                            move_history.pop() # it's for stockfish engine 
                            move_history.pop() # it's for stockfish engine 

                            print "--------- after take back: "
                            print board_history
                            print move_history
                            print "----------------------------------"


                            previous_board_click=""
                            board_click=""
                            mate_we_won = False
                            mate_we_lost = False

                            banner_do_move = False
                            do_user_move = False
                            banner_right_places = True

                            hint_text = ""
                        else:
                            print "cannot do takeback, len(board_history) = ",len(board_history)


                    if 6<x<89 and (183+22)<y<(216+22): # Hint button
#                        game_engine.setposition( move_history )
#                        am = game_engine.bestmove()
                        proc = stockfish.start_thinking_about_bestmove( move_history, difficulty )
                        #print "continues..."

                        show_board( board_state, 178, 40)
                        pygame.draw.rect(scr, lightgrey, (229*x_multiplier, 79*y_multiplier,\
                            200*x_multiplier,78*y_multiplier) )
                        pygame.draw.rect(scr, white, (227*x_multiplier, 77*y_multiplier,\
                            200*x_multiplier,78*y_multiplier) )
                        txt_large("Analysing...",227+55,77+8,grey)
                        show( "force-move", 247, 77+39 )
                        pygame.display.flip() # copy to screen

                        got_fast_result = False
                        while proc.poll()==None: # thinking
                            # event from system & keyboard
                            for event in pygame.event.get(): # all values in event list
                                if event.type == pygame.QUIT:
                                    pygame.display.quit()
                                    pygame.quit()
                                    sys.exit()

                            x,y   = pygame.mouse.get_pos() # mouse position
                            x = x/x_multiplier;
                            y = y/y_multiplier;

                            mbutton = pygame.mouse.get_pressed()
                            #txt_large("%d %d %s"%(x,y,str(mbutton)),0,0,black)
                            #pygame.display.flip() # copy to screen
                            if mbutton[0]==1 and 249<x<404 and 120<y<149: # pressed Force move button
                                hint_text = stockfish.get_fast_result( move_history )
                                got_fast_result = True
                                mbutton=(0,0,0)

                                break


                        if not got_fast_result:
                            hint_text = stockfish.get_result_of_thinking()

                        

                    if 6<x<78 and 244<y<272: # Save button
                        window = "save"
                        previous_board_click=""
                        board_click=""


    #---------------- new game dialog ----------------
    elif window=="new game":

        txt_large(  "Depth:", 203,115, green)
        show("depth"+str(difficulty+1),214,151)
        txt_large(  "<", 189,156, grey)
        txt_large(  ">", 265,156, grey)
        x0 = 213
        if difficulty==0:
            txt("Easiest",x0,191,grey)
        elif difficulty<4:
            txt("Easy",x0+6,191,grey)
        elif difficulty>18:
            txt("Very hard",x0-10,191,grey)
        elif difficulty>10:
            txt("Hard",x0+6,191,grey)
        else:
            txt("Normal",x0,191,grey)
        
        show("back",14,269)
        show("start",363,269)
        txt_large( "Color to play:", 175,232, green)
        if  play_white:
            show("white",184,269)
        else:
            show("black",184,269)

        
        if left_click:

            if 149<y<188:
                if x>233:
                    if difficulty<19: difficulty+=1
                    else: difficulty=0
                else:
                    if difficulty>0: difficulty-=1
                    else: difficulty=19


            if 268<y<(275+31):
                if 14<x<109: # <- back
                    window = "home"

                if 174<x<292: # blacl/white toggle
                    if play_white:
                        play_white = False
                    else:
                        play_white = True

                if 365<x<467: # start game ->
                    window = "game"
                    game_engine = stockfish.ini(difficulty)
                    board_state = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

                    move_history = [] 
                    board_history = [ board_state ]                  
                    terminal_text_line2 = "New game, depth="+ str(difficulty+1)
                    previous_board_click = ""
                    board_click = ""
                    do_user_move=False
                    do_ai_move = False
                    
                    #if play_white:
                    #    do_ai_move = False # first do user move
                    #else:
                    #    do_ai_move = True
                    conversion_dialog = False
                    mate_we_lost = False
                    mate_we_won = False
                    banner_do_move = False
                    game_process_just_started = True
                    banner_place_pieces = True


    left_click = False
    old_left_click = mbutton[0]

#    pygame.draw.line(scr, red, (0,0), (100,100), 3)
    pygame.display.flip() # copy to screen
    tt.sleep(0.005)
    T=datetime.now() - t
                