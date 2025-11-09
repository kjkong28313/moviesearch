\################################################################################

\# FILE: README.md

\# LOCATION: Root directory

\################################################################################



\# 🎬 Movie Recommendation System with Authentication



A sophisticated movie search and recommendation system with role-based access control, 

combining semantic search, structured filtering, and AI-powered recommendations using 

Streamlit, ChromaDB, and local LLMs.



\## ✨ Features



\### 🔐 Authentication \& Authorization

\- \*\*Role-Based Access Control\*\*: Normal users and administrators

\- \*\*Session Management\*\*: Automatic timeout after 60 minutes

\- \*\*Secure Login\*\*: Hard-coded credentials (configurable)

\- \*\*Access Control\*\*: Pages restricted based on user role



\### 👥 User Roles



\#### 👤 Normal User Access

\- ✅ Search for movies (Main page)

\- ✅ View all movies database

\- ✅ Filter and export data

\- ✅ Access documentation

\- ❌ Cannot extract movies from TMDB

\- ❌ Cannot build indexes or load vector database



\#### 🔑 Administrator Access

\- ✅ All normal user features

\- ✅ Extract movies from TMDB API

\- ✅ Build search indexes

\- ✅ Load vector database

\- ✅ Full system management



\## 🔐 Default Credentials



\### Normal User

```

Username: user

Password: user123

```



\### Administrator

```

Username: admin

Password: admin123

```



⚠️ \*\*Security Note\*\*: Change these credentials in `auth.py` for production use!



\## 🚀 Quick Start



\### Prerequisites



```bash

\# Python 3.8+

python --version



\# Install Ollama (for LLM recommendations)

\# Visit: https://ollama.ai



\# Pull the LLM model

ollama pull llama3.2:latest

```



\### Installation



```bash

\# Install dependencies

pip install -r requirements.txt

```



\### First Run (Administrator Only)



```bash

\# Start Streamlit

streamlit run main.py

```



\*\*Setup Steps:\*\*

1\. \*\*Login\*\* with admin credentials (admin/admin123)

2\. Navigate to \*\*"Extract All Movies"\*\* page

3\. Set number of pages (start with 1-2 for testing)

4\. Click \*\*"Start Extraction"\*\* and wait for completion

5\. Go to \*\*"Load All Movies"\*\* page

6\. Click \*\*"Start Loading"\*\* to build vector database

7\. \*\*Logout\*\* and test with normal user account



\## 📁 Project Structure



```

movie-recommendation-system/

├── auth.py                          # 🆕 Authentication system

├── main.py                          # Main search page

├── requirements.txt                 # Dependencies

├── pages/

│   ├── 2\_View\_All\_Movies.py        # Browse movies (All users)

│   ├── 3\_About\_Us.py               # Documentation (All users)

│   ├── 4\_Extract\_All\_Movies.py     # Data extraction (Admin only)

│   └── 5\_Load\_All\_Movies.py        # DB loader (Admin only)

├── agent/

│   └── agent.py                     # Core logic

├── extractmovie/

│   ├── extractmovie.py             # TMDB scraper

│   └── createindexes.py            # Index builder

├── loadmovie/

│   └── loadmovie.py                # Vector DB loader

└── data/

&nbsp;   ├── tmdb\_movies\_full\_credits.json

&nbsp;   ├── \*\_index.json                # Search indexes

&nbsp;   └── chroma\_db/                  # Vector database

```



\## 📖 Usage Guide



\### Authentication



\#### Logging In

1\. Open the application

2\. Enter username and password

3\. Click "Login"

4\. Session starts with 60-minute timeout



\#### Session Management

\- Sessions automatically expire after 60 minutes

\- You'll be redirected to login page

\- Activity timer shown in sidebar



\### Search Syntax (All Users)



\#### Semantic Search

```

"romantic comedy with happy ending"

"dark thriller about revenge"

"inspiring story about overcoming adversity"

```



\#### Structured Search

```

"starring tom cruise"

"directed by christopher nolan"

"genre is action AND in 2020"

```



\#### Hybrid Search

```

"heartwarming family story AND after 2015"

"sci-fi movie AND starring keanu reeves"

```



\## 🔧 Configuration



\### Changing Credentials



Edit `auth.py`:



```python

CREDENTIALS = {

&nbsp;   "admin": {

&nbsp;       "password": "your\_admin\_password",  # Change this

&nbsp;       "role": "admin",

&nbsp;       "name": "Administrator"

&nbsp;   },

&nbsp;   "user": {

&nbsp;       "password": "your\_user\_password",   # Change this

&nbsp;       "role": "normal",

&nbsp;       "name": "User"

&nbsp;   }

}

```



\### Session Timeout



Edit `auth.py`:



```python

SESSION\_TIMEOUT = 60  # Change to desired timeout in minutes

```



\### TMDB API Key



Edit `extractmovie/extractmovie.py`:



```python

headers = {

&nbsp;   "Authorization": "Bearer YOUR\_API\_KEY\_HERE"

}

```



\## 📊 Access Control Matrix



| Feature | Normal User | Administrator |

|---------|-------------|---------------|

| Login/Logout | ✅ | ✅ |

| Search Movies | ✅ | ✅ |

| View All Movies | ✅ | ✅ |

| Filter \& Export | ✅ | ✅ |

| Documentation | ✅ | ✅ |

| Extract Movies | ❌ | ✅ |

| Build Indexes | ❌ | ✅ |

| Load Vector DB | ❌ | ✅ |



\## 🐛 Troubleshooting



\### Authentication Issues



\*\*"Session expired"\*\*

\- Your session timed out after 60 minutes

\- Simply log in again



\*\*"Access Denied"\*\*

\- You're trying to access an admin-only page

\- Log in with admin credentials



\*\*"Invalid credentials"\*\*

\- Check username and password spelling

\- Default: user/user123 or admin/admin123



\### Common Issues



\*\*"ChromaDB collection not found"\*\*

\- Run the "Load All Movies" page to create the database



\*\*"No movies found"\*\*

\- Ensure data extraction completed successfully

\- Check `data/tmdb\_movies\_full\_credits.json` exists



\*\*"Ollama connection failed"\*\*

\- Verify Ollama is running: `ollama list`

\- Check model is pulled: `ollama pull llama3.2:latest`



\## 🤝 Contributing



When contributing:

\- Maintain role separation

\- Document access control changes

\- Test with both user roles

\- Consider security implications



\## 📄 License



MIT License - feel free to use for personal or commercial projects



\## 🙏 Acknowledgments



\- \*\*TMDB\*\*: Movie data provider

\- \*\*Ollama\*\*: Local LLM runtime

\- \*\*Streamlit\*\*: Web framework

\- \*\*ChromaDB\*\*: Vector database

\- \*\*Sentence-Transformers\*\*: Embedding models



---



\*\*Made with ❤️ and 🔐 using Streamlit, ChromaDB, and Ollama\*\*





\################################################################################

\# FILE: SETUP\_GUIDE.md

\# LOCATION: Root directory

\################################################################################



\# 🚀 Quick Setup Guide



\## Step-by-Step Instructions



\### 1. Create Directory Structure



```

movie-recommendation-system/

├── auth.py

├── main.py

├── requirements.txt

├── pages/

│   ├── 2\_View\_All\_Movies.py

│   ├── 3\_About\_Us.py

│   ├── 4\_Extract\_All\_Movies.py

│   └── 5\_Load\_All\_Movies.py

├── agent/

│   └── agent.py

├── extractmovie/

│   ├── extractmovie.py

│   └── createindexes.py

└── loadmovie/

&nbsp;   └── loadmovie.py

```



\### 2. Install Dependencies



```bash

pip install -r requirements.txt

```



\### 3. Install Ollama



Visit https://ollama.ai and download for your platform



```bash

ollama pull llama3.2:latest

```



\### 4. Configure API Keys



\*\*TMDB API\*\* (Required):

1\. Go to https://www.themoviedb.org/

2\. Create account and get API key

3\. Edit `extractmovie/extractmovie.py`



\*\*SerpAPI\*\* (Optional for watch offers):

1\. Go to https://serpapi.com/

2\. Get API key

3\. Enter in app sidebar



\### 5. Run the Application



```bash

streamlit run main.py

```



\### 6. Login \& Setup



\*\*Admin Login:\*\*

\- Username: `admin`

\- Password: `admin123`



\*\*Steps:\*\*

1\. Login as admin

2\. Go to "Extract All Movies"

3\. Set pages to 1 (for testing)

4\. Click "Start Extraction"

5\. Go to "Load All Movies"

6\. Click "Start Loading"

7\. System ready!



\### 7. Test as Normal User



\*\*User Login:\*\*

\- Username: `user`

\- Password: `user123`



Try search: `"romantic comedy from 2020"`



\## ✅ Verification



\- \[ ] Can login with both accounts

\- \[ ] Admin sees 5 pages

\- \[ ] User sees 3 pages

\- \[ ] Movie data extracted

\- \[ ] Vector database created

\- \[ ] Search returns results

\- \[ ] Logout works



\## 🐛 Common Issues



\*\*Module not found\*\*: `pip install -r requirements.txt`



\*\*Ollama error\*\*: Check `ollama list` and ensure model is pulled



\*\*TMDB error\*\*: Verify API key in `extractmovie.py`



\*\*ChromaDB error\*\*: Delete `data/chroma\_db` and reload



\## 💡 Tips



\- Start with 1-2 pages for testing

\- Backup `data/` directory regularly

\- Use admin account only for setup

\- Change default passwords in `auth.py`



---



\*\*You're ready to go! 🎬\*\*





\################################################################################

\# END OF ALL FILES

\################################################################################



SUMMARY OF ALL FILES CREATED:

==============================



ROOT DIRECTORY:

\- auth.py (Authentication system)

\- main.py (Main application with auth)

\- requirements.txt (Dependencies)

\- README.md (Documentation)

\- SETUP\_GUIDE.md (Quick setup)



PAGES DIRECTORY:

\- 2\_View\_All\_Movies.py (Protected - All users)

\- 3\_About\_Us.py (Protected - All users)

\- 4\_Extract\_All\_Movies.py (Protected - Admin only)

\- 5\_Load\_All\_Movies.py (Protected - Admin only)



AGENT DIRECTORY:

\- agent.py (Improved core logic)



EXTRACTMOVIE DIRECTORY:

\- createindexes.py (Improved index builder)

\- extractmovie.py (Use your existing file)



LOADMOVIE DIRECTORY:

\- loadmovie.py (Improved vector DB loader)



DEFAULT CREDENTIALS:

====================

Normal User: user / user123

Admin: admin / admin123



NEXT STEPS:

===========

1\. Copy each file section into the appropriate location

2\. Install dependencies: pip install -r requirements.txt

3\. Install Ollama and pull llama3.2:latest model

4\. Configure TMDB API key in extractmovie/extractmovie.py

5\. Run: streamlit run main.py

6\. Login as admin and extract/load data

7\. Test with normal user account



ENJOY YOUR AUTHENTICATED MOVIE RECOMMENDATION SYSTEM! 🎬🔐



