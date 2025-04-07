# **User GPU Records Extraction Tool**

This script extracts GPU job records for a specific **user** within a given **date range**.

## **Usage**  

### **Basic Command**
```sh
python userusage.py <start_date> <end_date> <username>
```
- `<start_date>`: Start date in `YYYY-MM-DD` format  
- `<end_date>`: End date in `YYYY-MM-DD` format  
- `<username>`: The username to filter records  

### **Example**
```sh
python userusage.py 2023-12-15 2024-02-10 johndoe
```
This will display the first few records for **user 'johndoe'** between **Dec 15, 2023, and Feb 10, 2024**.

---

## **Optional Arguments**
| Option | Description |
|--------|-------------|
| `-o, --output <file>` | Save results to a CSV file |

### **Example with Output File**
```sh
python userusage.py 2023-12-15 2024-02-10 johndoe -o records.csv
```
This will save the records to `records.csv`.

---

## **Error Handling**
- If no records are found, the script will display:
  ```
  No records found for the given criteria.
  ```
- If an invalid date format is entered, it will display:
  ```
  Error: Invalid date format. Please use YYYY-MM-DD.
  ```

