import sys
import os
import glob
import pickle

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print 'Usage:', sys.argv[0], 'pickleFile, testFileOrFolder'
    else:
        if os.path.isfile(sys.argv[1]):
            # load pickle
            predictor = pickle.load(open(sys.argv[1], 'r'))
            num_spam = 0.0
            num_ham = 0.0
            count = 0
            if os.path.isdir(sys.argv[2]):
                # predict all files in folder
                for f in glob.glob(sys.argv[2]+'/*'):
                    p = predictor.predict(f)
                    print f, 'is', p
                    if p:
                        num_spam += 1
                    else:
                        num_ham += 1
                    count += 1
            elif os.path.isfile(sys.argv[2]):
                # predict this file
                print sys.argv[2], 'is', predictor.predict(sys.argv[2])
            else:
                print 'test file illegal'
            print "READ AND SAVE RESULTS:"
            print "======================"
            print "num spam is: " + str(num_spam/count)
            print "num ham is: " + str(num_ham/count)
        else:
            print 'pickle file illegal'
