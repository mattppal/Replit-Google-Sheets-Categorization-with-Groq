from replit import db

if __name__ == "__main__":
  for k in db.keys():
    del db[k]
