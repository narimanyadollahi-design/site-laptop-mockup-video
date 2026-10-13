const http=require('http'),fs=require('fs'),path=require('path');
const root=path.resolve(process.argv[2]||'site');
const T={'.html':'text/html','.js':'text/javascript','.css':'text/css','.png':'image/png','.jpg':'image/jpeg','.woff2':'font/woff2','.mp4':'video/webm','.json':'application/json'};
http.createServer((q,r)=>{let u=decodeURIComponent(q.url.split('?')[0]);if(u.endsWith('/'))u+='index.html';let f=path.join(root,u);
if(!fs.existsSync(f)){r.writeHead(404);return r.end('nf');}
const s=fs.statSync(f),t=T[path.extname(f)]||'application/octet-stream',rg=q.headers.range;
if(rg){const m=/bytes=(\d*)-(\d*)/.exec(rg);let a=+m[1]||0,b=m[2]?+m[2]:s.size-1;r.writeHead(206,{'Content-Type':t,'Content-Range':`bytes ${a}-${b}/${s.size}`,'Accept-Ranges':'bytes','Content-Length':b-a+1});fs.createReadStream(f,{start:a,end:b}).pipe(r);}
else{r.writeHead(200,{'Content-Type':t,'Content-Length':s.size,'Accept-Ranges':'bytes'});fs.createReadStream(f).pipe(r);}
}).listen(+process.argv[3]||8099);
