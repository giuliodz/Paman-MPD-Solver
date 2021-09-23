if __name__ == '__main__':
    import os
    SAMPLES = 100
    import sys
    import subprocess
    # from pacman import runGames
    # runGames(layout, pacman, ghosts, display, 50, record, numTraining = 0, catchExceptions=False, timeout=30 )
    totRate = 0
    lowestSample = 1.0
    highestSample = 0.0
    rates = []
    for i in range(0,SAMPLES):
        winRate = subprocess.check_output(["C:\Python27\python.exe", "pacman.py", "-q", "-n", "25", "-p", "MDPAgent", "-l", "smallGrid"])
        # stream = os.popen('C:\Python27\python.exe pacman.py -q -n 50 -p MDPAgent -l mediumClassic')
        # winRate = stream.read()
        r=''
        is_next = False
        for rate in winRate:
            #If string is non empty, convert to float and add
            if rate.strip() != '':
                # print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
                # print(rate)
                if rate.strip() =='~':
                    is_next = True
                    
                if is_next:
                    if rate.strip() != '~':
                        r += rate.strip()
                

        print(r)
        winRate = float(r)
        if winRate < lowestSample:
            lowestSample = winRate
        if winRate > highestSample:
            highestSample = winRate
        rates.append(winRate)
        print(winRate)
        print( i + 1)
        totRate += winRate

    print "Number of run: {0}".format(str(SAMPLES))
    print "Average win rate: {0}".format(str(totRate/SAMPLES))
    print "Lowest sample win rate: {0}".format(str(lowestSample))
    print "Highest sample win rate: {0}".format(str(highestSample))
    print "Standard deviation:{0}".format(rates)

        