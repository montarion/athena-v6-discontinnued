so, a modular assistant!

athena will consist of:
- **core** systems:
    - Networking
    - Databases
    - Module discovery
    - Task system
    - Logger

- **modules**:
    These get planned into the task system, and periodically produce output.
    - Anime
    - Weather
    - Calendar
    - News
    - Discord (also a user interface)
    - Spotify

- **agents**:
    Smaller standalone programs that enhance or support managers, but are too generic to include with a module.
    - Compression(video, photo)
    - Distributed Computing
    - File transfers
    modules can request these agents, but should work fine, albeit hampered, without the agents. if not, the functionality should be included in the module.

- **user interfaces**:
    These are, well, user interfaces. of any kind.
    - Website
    - Discord(Also a manager)
    - Speech
        - this is an example, don't worry about it
