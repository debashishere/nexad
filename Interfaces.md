

=> Create Ads 
    - Image 
    - Text 
    - Svg

-Create Record in Redos with Lock(awaiting for AI agent)
- Agent Acts of the newly Created Ad
- Recod Store to DB 
- Respond to the User 

We will use Aws Local Stack SQS to Push Each Action to the Queue for Create Action 
    - Respond instately Creation in Progress. Send dedicated push notification if after all actions if required.

=> Update Ads

=> Archive Ads

=> Track ads stats of Citation Count, Engagement Count, Conversation Rate, Click Per Engagement, ...

=> Competitor Reachrach and Live Agent Training on Ad-Creating ( Re-informent Learning)

=> Compititor Reseach 
    -Use advance AI Techniques 




- Project Follow Modular Architecture 
- Async Code are written with error handlings 
- Service Files are Created by Accumulating Similar Functionalities Together 
- MCP Controller files contains the Core Controller Logics 
- Clear Boundary of Packages Should be drawn 
( 
    - Business logics lives in Service Files
    - Data & related manupulation logics should be inside data-repositories or DB Module 
    - Karnel Sanbox Creation & Execution logics should be sepearated 
    
)

- CDN Management and Opearional logics should be contains on its own module


