Heart Room – Protection Pack

Files:
- HeartRoom_Playbook_Caesar_Protocol.md  (this is the operational playbook)
- heartroom_2025-08-14.txt.docx          (your uploaded archive transcript)

Integrity:
- SHA256 (archive): e6f0f7c7caa410854c401c3d66dd1e135f696ba24bf92068d834d79549b6827a

Termux (Android) quick start:
  pkg update && pkg upgrade -y
  pkg install -y openssl
  sha256sum heartroom_2025-08-14.txt.docx
  openssl enc -aes-256-cbc -salt -in HeartRoom_Playbook_Caesar_Protocol.md -out HeartRoom_Playbook_Caesar_Protocol.enc

Keep passphrases offline. Store one encrypted copy offline (USB) and one in the cloud with a different key.
