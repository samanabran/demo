export interface Caption {
  id: string;
  text: string;
  durationS: number;
}

export const captions: Caption[] = [
  {
    "id": "01-intro",
    "text": "This is the complete walkthrough of property syndication in the SGC Property Management module: testing connectivity to Bayut, Property Finder, and Dubizzle, publishing a real listing and capturing a real lead, and ingesting a sample partner feed.",
    "durationS": 25.61
  },
  {
    "id": "02-rapidapi-intro",
    "text": "First, connectivity. Each portal connector stores a RapidAPI key and can test whether that portal's market data API is actually reachable, with one click.",
    "durationS": 12.84
  },
  {
    "id": "03-rapidapi-bayut",
    "text": "Bayut. Clicking Test RapidAPI Connection fires a real request and confirms the key is accepted.",
    "durationS": 8.41
  },
  {
    "id": "04-rapidapi-pf",
    "text": "Property Finder. Same test, same button, a different portal.",
    "durationS": 6.54
  },
  {
    "id": "05-rapidapi-dubizzle",
    "text": "And Dubizzle. All three portals, verified live, each logged with its own timestamp and result.",
    "durationS": 8.23
  },
  {
    "id": "06-rapidapi-note",
    "text": "This connectivity test is separate from actual listing syndication. It only confirms the key and host are working, nothing more.",
    "durationS": 10.88
  },
  {
    "id": "07-publish-unpublished",
    "text": "Now, publishing a real listing. Here is Palm Jumeirah Residences, Unit 507, currently unpublished.",
    "durationS": 9.86
  },
  {
    "id": "08-publish-click",
    "text": "Clicking Publish makes it live on the public website immediately.",
    "durationS": 4.96
  },
  {
    "id": "09-publish-confirm",
    "text": "The button now reads Unpublish, confirming the property is public.",
    "durationS": 5.65
  },
  {
    "id": "10-public-search",
    "text": "Switching to the public website, we search for Unit 507, exactly as a real buyer would.",
    "durationS": 13.03
  },
  {
    "id": "11-public-detail",
    "text": "Here's the listing, live, with the same price and details we just published.",
    "durationS": 8.68
  },
  {
    "id": "12-inquiry-open",
    "text": "Clicking Inquire Now reveals a gated lead capture form right on the listing page.",
    "durationS": 7.86
  },
  {
    "id": "13-inquiry-fill",
    "text": "We fill it out as a real visitor: name, email, phone, and a message.",
    "durationS": 7.5
  },
  {
    "id": "14-inquiry-submit",
    "text": "Submitting sends this straight into Odoo as a new inquiry, linked to this exact property.",
    "durationS": 8.28
  },
  {
    "id": "15-gap-fix-intro",
    "text": "Here's a real gap we found and fixed. Before, there was no way to see these captured leads from the property record at all.",
    "durationS": 9.03
  },
  {
    "id": "16-smart-button-click",
    "text": "So we added a Website Inquiries button. It stays hidden until a property actually has an inquiry, then it appears automatically.",
    "durationS": 10.13
  },
  {
    "id": "17-smart-button-proof",
    "text": "One click, and there's the lead we just submitted, correctly linked to this exact unit.",
    "durationS": 6.65
  },
  {
    "id": "18-feed-intro",
    "text": "Now, the other side of syndication: pulling listings in from a partner feed. This is the sample feed used to test the ingestion pipeline.",
    "durationS": 10.38
  },
  {
    "id": "19-feed-config",
    "text": "The Bayut connector points its Inbound Feed URL at this sample file, three properties covering the realistic cases the parser needs to handle.",
    "durationS": 10.65
  },
  {
    "id": "20-feed-run",
    "text": "Running the scheduled action processes the feed right now, the same job that would run automatically on a real schedule.",
    "durationS": 14.17
  },
  {
    "id": "21-feed-result",
    "text": "And here they are, three new properties, imported directly from the feed and flagged as feed sourced.",
    "durationS": 8.06
  },
  {
    "id": "22-closing",
    "text": "Connectivity, publishing, lead capture, and feed ingestion: the full syndication loop, all working end to end inside one module.",
    "durationS": 11.78
  }
];
