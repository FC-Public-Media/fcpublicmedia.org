# `machines/editing-bay-1/share.ps1`

Moved out of the file. Unreviewed.

## 1

Above `param(`

share.ps1 -- the drop shares this bay serves over SMB.

share.ps1 status     each share: path, who may do what, and how a Mac connects
share.ps1 install    make what is missing: the `enhance` account and share

`enhance` is E:, "TO ENHANCE", the 1 TB Drobo LUN: a slush that recordings are
dropped into and evicted from all the time. People write into it; they need
not read it. It is served to a local account, `enhance`, because this bay's
own account is a Microsoft account, and over SMB that wants the account's
email and online password, which Macs have never got right.

The account's password is typed at install and never written. Keep it in the
password manager. A Mac connects to smb://<this bay>/enhance as `enhance`.

`install` needs an administrator. From a plain shell it asks Windows for it
(one prompt) and shows its log when done. Running it twice changes nothing.

Windows PowerShell 5.1, no modules. ASCII only.
