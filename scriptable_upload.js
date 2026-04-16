// Scriptable GitHub Upload

const owner = "DEIN_OWNER";
const repo = "DEIN_REPO";
const branch = "main";

const tokenAlert = new Alert();
tokenAlert.title = "GitHub Token";
tokenAlert.addTextField("Token");
tokenAlert.addAction("OK");
await tokenAlert.present();

const token = tokenAlert.textFieldValue(0);

const file = await DocumentPicker.open();

const fm = FileManager.local();
const data = fm.read(file);
const base64 = data.toBase64String();

const name = file.split("/").pop();

const url = `https://api.github.com/repos/${owner}/${repo}/contents/${name}?ref=${branch}`;

let sha = null;

try{
let req = new Request(url);
req.headers = {Authorization:`Bearer ${token}`};
let res = await req.loadJSON();
sha = res.sha;
}catch(e){}

let body = {
message: "upload "+name,
content: base64,
branch: branch
};

if(sha) body.sha = sha;

let req2 = new Request(url);
req2.method = "PUT";
req2.headers = {
Authorization:`Bearer ${token}`,
"Content-Type":"application/json"
};
req2.body = JSON.stringify(body);

let result = await req2.loadString();

QuickLook.present(result);
