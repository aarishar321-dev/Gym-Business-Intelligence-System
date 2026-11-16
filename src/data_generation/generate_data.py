import pandas as pd
import numpy as np
from pathlib import Path
from faker import Faker


SEED = 42
N_MEMBERS = 1000

np.random.seed(SEED)
Faker.seed(SEED)

fake = Faker("en_IN")


OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


MALE_NAMES = [
    "Arjun Kumar",
    "Karthik Krishnan",
    "Vignesh Rajan",
    "Praveen Kumar",
    "Sanjay Narayanan",
    "Surya Prasad",
    "Dinesh Subramanian",
    "Harish Srinivasan",
    "Naveen Kumar",
    "Ashwin Raj",
    "Vijay Krishnan",
    "Sathish Kumar",
    "Rohit Sharma",
    "Aditya Prasad",
    "Rahul Varma",
    "Gokul Raj",
    "Siddharth Iyer",
    "Manoj Kumar",
    "Ajay Krishnan",
    "Aravind Rajan",
    "Vishal Kumar",
    "Nikhil Raj",
    "Akash Prasad",
    "Bharath Kumar",
    "Deepak Narayanan",
    "Dhanush Raj",
    "Gautham Krishnan",
    "Jeevan Kumar",
    "Akhil Menon",
    "Abhinav Rao",
    "Rakesh Kumar",
    "Varun Raj",
    "Suraj Nair",
    "Abhishek Menon",
    "Suresh Kumar",
    "Madhan Raj",
    "Prakash Kumar",
    "Ramesh Krishnan",
    "Sriram Narayanan",
    "Balaji Kumar",
    "Nithin Raj",
    "Vasanth Kumar",
    "Lokesh Krishnan",
    "Mohan Raj",
    "Raghav Prasad",
    "Vivek Kumar",
    "Ranjith Raj",
    "Santhosh Kumar",
    "Kavin Raj",
    "Ashwin Kumar",
    "Hari Krishnan",
    "Surya Narayanan",
    "Raghu Kumar",
    "Manikandan Raj",
    "Sakthi Kumar",
    "Pranav Menon",
    "Aakash Raj",
    "Tarun Kumar",
    "Yashwanth Rao",
    "Naveen Raj",
    "Rithvik Kumar",
    "Vishnu Prasad",
    "Adithya Raj",
    "Mithun Kumar",
    "Sanjay Raj",
    "Rohit Kumar",
    "Kiran Kumar",
    "Naveen Prasad",
    "Siddharth Raj",
    "Varun Kumar",
    "Vignesh Kumar",
    "Karthik Raj",
    "Pradeep Kumar",
    "Sathya Raj",
    "Girish Kumar",
    "Ravi Shankar",
    "Vijay Kumar",
    "Arun Kumar",
    "Suresh Raj",
    "Ganesh Kumar",
    "Muralidharan Raj",
    "Senthil Kumar",
    "Saravanan Raj",
    "Karthikeyan Kumar",
    "Bala Krishnan",
    "Siva Kumar",
    "Sivakumar Raj",
    "Rajesh Kumar",
    "Manoj Raj",
    "Vimal Kumar",
    "Dharshan Raj",
    "Naren Kumar",
    "Suraj Kumar",
    "Aravind Kumar",
    "Joel Joseph",
    "Joseph Thomas",
    "Daniel Mathew",
    "Kevin George",
    "Samuel Paul",
    "David Thomas",
    "Aaron Joseph",
    "Michael George",
    "Joshua Mathew",
    "Ryan Fernandes",
    "Nathan Joseph",
    "Christopher Thomas",
    "Andrew George",
    "Matthew Paul",
    "Benjamin Joseph",
    "Jonathan Mathew",
    "Imran Khan",
    "Amaan Ahmed",
    "Faizan Rahman",
    "Sameer Khan",
    "Azeem Hussain",
    "Mohammed Rahman",
    "Irfan Ahmed",
    "Rizwan Khan",
    "Yusuf Mohammed",
    "Zaid Hussain",
    "Arman Khan",
    "Rehan Ahmed",
    "Danish Rahman",
    "Adil Khan",
    "Sahil Ahmed",
    "Faisal Rahman",
    "Tariq Hussain",
    "Kabir Khan",
    "Omar Ahmed",
    "Rayyan Rahman"
]


FEMALE_NAMES = [
    "Keerthana Kumar",
    "Divya Krishnan",
    "Harini Rajan",
    "Ananya Prasad",
    "Shruthi Iyer",
    "Nandhini Subramanian",
    "Deepika Kumar",
    "Kavya Raj",
    "Swathi Narayanan",
    "Priya Krishnan",
    "Aishwarya Kumar",
    "Pavithra Rajan",
    "Ramya Srinivasan",
    "Shreya Prasad",
    "Meghana Rao",
    "Anjali Menon",
    "Sowmya Nair",
    "Janani Kumar",
    "Vaishnavi Krishnan",
    "Lakshmi Narayanan",
    "Dhanya Menon",
    "Niveditha Raj",
    "Monisha Kumar",
    "Sahana Rao",
    "Aparna Nair",
    "Anusha Kumar",
    "Pooja Krishnan",
    "Sandhya Rajan",
    "Sangeetha Kumar",
    "Revathi Narayanan",
    "Bhavana Rao",
    "Mahalakshmi Raj",
    "Swetha Kumar",
    "Sruthi Raj",
    "Pavani Prasad",
    "Deepa Krishnan",
    "Meena Kumar",
    "Shalini Raj",
    "Reshma Menon",
    "Nithya Narayanan",
    "Sharmila Kumar",
    "Archana Raj",
    "Lavanya Krishnan",
    "Gayathri Kumar",
    "Sindhu Rajan",
    "Ranjani Narayanan",
    "Hema Krishnan",
    "Kirthika Kumar",
    "Aarthi Raj",
    "Janani Krishnan",
    "Madhumitha Kumar",
    "Roshini Raj",
    "Aparna Krishnan",
    "Preethi Kumar",
    "Sowmya Raj",
    "Anitha Narayanan",
    "Revathi Kumar",
    "Shivani Raj",
    "Nandita Krishnan",
    "Kavitha Kumar",
    "Harshitha Raj",
    "Mounika Rao",
    "Srilakshmi Kumar",
    "Bhavya Raj",
    "Sneha Krishnan",
    "Riya Kumar",
    "Tanisha Raj",
    "Ishita Prasad",
    "Aditi Kumar",
    "Neha Raj",
    "Rhea Krishnan",
    "Niharika Rao",
    "Shreya Kumar",
    "Meera Narayanan",
    "Ishwarya Raj",
    "Swara Kumar",
    "Aaradhya Krishnan",
    "Nitya Raj",
    "Sanjana Kumar",
    "Akshara Rao",
    "Ananya Raj",
    "Maya Krishnan",
    "Diya Kumar",
    "Radhika Raj",
    "Madhavi Narayanan",
    "Kavya Kumar",
    "Anu Krishnan",
    "Priyanka Raj",
    "Sahana Kumar",
    "Deepthi Rao",
    "Haritha Krishnan",
    "Shilpa Kumar",
    "Amritha Raj",
    "Jennifer Joseph",
    "Maria Thomas",
    "Merlin George",
    "Catherine Mathew",
    "Rachel Joseph",
    "Rebecca Thomas",
    "Hannah George",
    "Sarah Mathew",
    "Joanna Joseph",
    "Esther Paul",
    "Emily Thomas",
    "Grace Joseph",
    "Anna George",
    "Elizabeth Mathew",
    "Jessica Thomas",
    "Nicole Joseph",
    "Amanda George",
    "Michelle Paul",
    "Ayesha Khan",
    "Sana Ahmed",
    "Zoya Rahman",
    "Fatima Khan",
    "Hiba Ahmed",
    "Maryam Rahman",
    "Saira Khan",
    "Noor Ahmed",
    "Alisha Hussain",
    "Fathima Rahman",
    "Shabana Khan",
    "Afreen Ahmed",
    "Nazia Hussain",
    "Inaya Khan",
    "Mariam Ahmed",
    "Aaliya Rahman",
    "Hafsa Khan",
    "Sara Hussain",
    "Madiha Ahmed",
    "Rida Rahman",
    "Areeba Khan",
    "Amina Hussain"
]


GENDERS = [
    "Male",
    "Female",
    "Other"
]


ACQUISITION_SOURCES = [
    "WhatsApp",
    "Instagram",
    "Google",
    "Referral",
    "Walk-in",
    "Website"
]


members = []

used_phone_numbers = set()


today = pd.Timestamp.today().normalize()

start_date = (
    today - pd.DateOffset(months=18)
)

number_of_days = (
    today - start_date
).days


for i in range(1, N_MEMBERS + 1):

    member_id = f"MEM{i:04d}"


    gender = np.random.choice(
        GENDERS,
        p=[0.55, 0.43, 0.02]
    )


    if gender == "Male":

        name = np.random.choice(
            MALE_NAMES
        )

    elif gender == "Female":

        name = np.random.choice(
            FEMALE_NAMES
        )

    else:

        name = np.random.choice(
            MALE_NAMES + FEMALE_NAMES
        )


    date_of_birth = fake.date_of_birth(
        minimum_age=18,
        maximum_age=60
    )


    while True:

        first_digit = np.random.choice(
            ["6", "7", "8", "9"]
        )

        remaining_digits = "".join(
            np.random.choice(
                list("0123456789"),
                size=9
            )
        )

        phone = (
            "+91"
            + first_digit
            + remaining_digits
        )

        if phone not in used_phone_numbers:

            used_phone_numbers.add(phone)

            break


    random_days = np.random.randint(
        0,
        number_of_days + 1
    )


    join_date = (
        start_date
        + pd.Timedelta(
            days=int(random_days)
        )
    )


    join_datetime = pd.Timestamp(
        join_date
    )


    max_seconds = int(
        (
            pd.Timestamp.now()
            - join_datetime
        ).total_seconds()
    )


    if max_seconds > 0:

        random_seconds = np.random.randint(
            0,
            max_seconds + 1
        )

        created_at = (
            join_datetime
            + pd.Timedelta(
                seconds=int(random_seconds)
            )
        )

    else:

        created_at = pd.Timestamp.now()


    acquisition_source = np.random.choice(
        ACQUISITION_SOURCES,
        p=[
            0.20,
            0.20,
            0.15,
            0.20,
            0.15,
            0.10
        ]
    )


    members.append({
        "member_id": member_id,
        "name": name,
        "date_of_birth": date_of_birth,
        "gender": gender,
        "phone": phone,
        "join_date": join_date,
        "acquisition_source": acquisition_source,
        "created_at": created_at
    })


members_df = pd.DataFrame(
    members
)


output_file = (
    OUTPUT_DIR / "members.csv"
)


members_df.to_csv(
    output_file,
    index=False
)


print("Member dataset generated successfully!")

print(f"Rows: {len(members_df)}")

print(f"Columns: {len(members_df.columns)}")

print(f"Saved to: {output_file}")


print("\nFirst 5 rows:")

print(
    members_df.head()
)


print("\nMissing values:")

print(
    members_df.isnull().sum()
)


print("\nDuplicate member IDs:")

print(
    members_df["member_id"]
    .duplicated()
    .sum()
)


print("\nDuplicate phone numbers:")

print(
    members_df["phone"]
    .duplicated()
    .sum()
)


print("\nJoin date range:")

print(
    members_df["join_date"].min(),
    "to",
    members_df["join_date"].max()
)


print("\nAcquisition source distribution:")

print(
    members_df["acquisition_source"]
    .value_counts()
)


print("\nGender distribution:")

print(
    members_df["gender"]
    .value_counts()
)