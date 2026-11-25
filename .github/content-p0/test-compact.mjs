import {boundedDistance} from './compact-band.mjs';
function full(a,b){let d=Array.from({length:a.length+1},(_,i)=>Array.from({length:b.length+1},(_,j)=>i===0?j:j===0?i:0));for(let i=1;i<=a.length;i++)for(let j=1;j<=b.length;j++)d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+Number(a[i-1]!==b[j-1]));return d[a.length][b.length]}
let words=[""];for(let n=1;n<=5;n++)for(let i=0;i<2**n;i++)words.push(i.toString(2).padStart(n,"0"));
let checks=0,failures=[];
for(let a of words)for(let b of words)for(let k=0;k<=6;k++){let actual=boundedDistance([...a],[...b],k),expected=Math.min(full(a,b),k+1);checks++;if(actual!==expected)failures.push({a,b,k,actual,expected})}
console.log(JSON.stringify({checks,failures,scope:"Exact article implementation, all ordered binary strings lengths 0–5, k=0–6"}));if(failures.length)process.exit(1);
